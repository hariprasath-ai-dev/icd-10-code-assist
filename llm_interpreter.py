import json
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMInterpreter:
    def __init__(self, provider="gemini"):
        """
        Initialize LLM Interpreter with specified provider.
        
        Args:
            provider: "gemini" or "openrouter"
        """
        self.provider = provider
        
        if provider == "openrouter":
            self.api_key = os.getenv("OPEN_ROUTER_KEY")
            self.url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-thinking-2507")
            logger.info(f"LLMInterpreter initialized with OpenRouter model: {self.model}")
        else:  # gemini
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            logger.info("LLMInterpreter initialized with Gemini Direct")

    def interpret_meaning(self, structured_doc):
        prompt = f"""
        Extract clinical concepts from the medical record.
        Return ONLY valid JSON. No commentary.

        STRICT RULES:
        1. 'confirmed_diagnoses': List active/acute findings.
        2. 'procedures': List ALL procedures including imaging (CT, X-ray, MRI), surgeries, interventions, and therapeutic procedures. Use standard medical procedure names.
        3. Use standard clinical naming (e.g., 'Hypertension', 'Maxillary fracture', 'Appendectomy', 'Central line insertion').
        4. Capture 'symptoms' (patient complaints) and 'history_conditions' (chronic/past).
        5. For procedures, be specific about approach, body part, and method when mentioned.

        Schema:
        {{
          "confirmed_diagnoses": [],
          "suspected_conditions": [],
          "symptoms": [],
          "history_conditions": [],
          "procedures": []
        }}
        Structured Doc: {json.dumps(structured_doc)}
        """
        
        if self.provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://icd-coding-assistant.local",
                "X-Title": "ICD-10-CM Coding Assistant"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a clinical concept extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                text = response.json()['choices'][0]['message']['content']
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            else:
                raise Exception(f"OpenRouter API Error: {response.text}")
        else:  # gemini
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                text = response.json()['candidates'][0]['content']['parts'][0]['text']
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            else:
                raise Exception(f"Gemini API Error: {response.text}")

    def generate_explanation(self, codes_by_category, applied_refs, clinical_map):
        prompt = f"""
        Generate a concise clinical rationale for these code assignments.
        
        Assigned Codes: {json.dumps(codes_by_category)}
        Clinical Findings: {json.dumps(clinical_map)}
        
        INSTRUCTIONS:
        - Link each code category to specific findings in the medical record
        - Explain the clinical reasoning for code selection
        - Focus ONLY on why codes WERE selected based on documentation
        - Be concise and professional
        - DO NOT discuss codes that were not assigned
        - DO NOT mention missing codes or incomplete datasets
        - DO NOT include "Why not other codes" sections
        
        Format as clear paragraphs organized by category.
        """
        
        if self.provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://icd-coding-assistant.local",
                "X-Title": "ICD-10-CM Coding Assistant"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a medical coding explanation assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter API Error: {response.text}")
        else:  # gemini
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception(f"Gemini API Error: {response.text}")

    def refine_results(self, initial_results, clinical_map):
        prompt = f"""
        STRICT VALIDATION of code assignments.
        Initial Assignment: {json.dumps(initial_results)}
        Clinical Data: {json.dumps(clinical_map)}
        
        VALIDATION RULES:
        1. KEEP only codes explicitly supported by findings in the Clinical Data
        2. REMOVE any codes not directly supported by documentation
        3. For procedures, include both ICD-10-CM Z-codes and ICD-10-PCS codes when applicable
        4. Categories: "Diagnoses", "Suspected Conditions", "Symptoms", "Signs", "History", "Procedures/Imaging"
        5. Return ONLY a JSON object with validated codes
        
        CRITICAL: Focus only on what IS documented. Never mention what is missing or not provided.
        """
        
        if self.provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://icd-coding-assistant.local",
                "X-Title": "ICD-10-CM Coding Assistant"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a medical coding validation assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                text = response.json()['choices'][0]['message']['content']
                text = text.replace("```json", "").replace("```", "").strip()
                try:
                    return json.loads(text)
                except:
                    return initial_results
            return initial_results
        else:  # gemini
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                text = response.json()['candidates'][0]['content']['parts'][0]['text']
                text = text.replace("```json", "").replace("```", "").strip()
                try:
                    return json.loads(text)
                except:
                    return initial_results
            return initial_results
