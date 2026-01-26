import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMInterpreter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

    def interpret_meaning(self, structured_doc):
        prompt = f"""
        Extract clinical concepts from the medical record.
        Return ONLY valid JSON. No commentary.

        STRICT RULES:
        1. 'confirmed_diagnoses': List active/acute findings.
        2. 'procedures': List imaging (CT, X-ray, MRI) and surgeries. Use common clinical names (e.g., 'CT Chest').
        3. Use standard clinical naming (e.g., 'Hypertension', 'Maxillary fracture').
        4. Capture 'symptoms' (patient complaints) and 'history_conditions' (chronic/past).

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
        Generate a concise human-readable explanation for these ICD-10-CM assignments.
        Data: {json.dumps(codes_by_category)}
        Clinical findings: {json.dumps(clinical_map)}
        Link each category of codes to the specific findings in the report. 
        Explain the clinical rationale for why these codes were selected from the documentation.
        """
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(self.url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Gemini API Error: {response.text}")

    def refine_results(self, initial_results, clinical_map):
        prompt = f"""
        STRICT REVIEW AND CLEANUP of ICD-10-CM assignments.
        Initial Assignment: {json.dumps(initial_results)}
        Clinical Data: {json.dumps(clinical_map)}
        
        GOAL: Eliminate hallucinations and ensure 100% documentation support.
        
        RULES:
        1. REMOVE any code not explicitly supported by a finding in the 'Clinical Data'.
        2. DO NOT hallucinate codes based on general knowledge; only use what is in the report.
        3. For 'Procedures/Imaging', map to relevant Z-codes (e.g., Z01.81 for imaging) or R-codes for findings.
        4. Categories: "Diagnoses", "Suspected Conditions", "Symptoms", "Signs", "History", "Procedures/Imaging".
        5. Return ONLY a JSON object.
        """
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
