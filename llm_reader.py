import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMReader:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

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
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = requests.post(self.url, headers=headers, json=payload)
        if response.status_code == 200:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            # Clean markdown
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        else:
            raise Exception(f"Gemini API Error: {response.text}")

    def get_structured_data(self, raw_text):
        return self.structure_document(raw_text)
