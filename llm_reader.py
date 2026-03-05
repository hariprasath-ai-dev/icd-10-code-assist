import json
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMReader:
    def __init__(self, provider="gemini"):
        """
        Initialize LLM Reader with specified provider.
        
        Args:
            provider: "gemini" or "openrouter"
        """
        self.provider = provider
        
        if provider == "openrouter":
            self.api_key = os.getenv("OPEN_ROUTER_KEY")
            self.url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-thinking-2507")
            logger.info(f"LLMReader initialized with OpenRouter model: {self.model}")
        else:  # gemini
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            logger.info("LLMReader initialized with Gemini Direct")

    def structure_document(self, raw_text):
        prompt = f"""
        Convert the following raw medical record into structured documentation.
        Return ONLY valid JSON. No commentary.
        Schema:
        {{
          "chief_complaint": "",
          "history_of_present_illness": "",
          "assessment": "",
          "plan": "",
          "provider_diagnoses_text": "",
          "other_notes": ""
        }}
        Raw Text: {raw_text}
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
                    {"role": "system", "content": "You are a medical documentation assistant. Return only valid JSON."},
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
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                text = response.json()['candidates'][0]['content']['parts'][0]['text']
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            else:
                raise Exception(f"Gemini API Error: {response.text}")

    def get_structured_data(self, raw_text):
        return self.structure_document(raw_text)
