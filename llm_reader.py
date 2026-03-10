import logging
import os

import requests
from dotenv import load_dotenv

from llm_contracts import (
    DOCUMENT_SCHEMA,
    build_groq_response_format,
    normalize_document_payload,
    parse_json_text,
)
from provider_config import get_provider_model

load_dotenv()

logger = logging.getLogger(__name__)


class LLMReader:
    def __init__(self, provider="gemini"):
        """
        Initialize LLM Reader with specified provider.

        Args:
            provider: "gemini" or "groq"
        """
        self.provider = provider

        if provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY")
            self.url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = get_provider_model("groq")
            logger.info("LLMReader initialized with Groq model: %s", self.model)
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.model = get_provider_model("gemini")
            self.url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                f"?key={self.api_key}"
            )
            logger.info("LLMReader initialized with Gemini model: %s", self.model)

    def _groq_messages(self, prompt):
        return [
            {
                "role": "system",
                "content": (
                    "You are a medical documentation assistant. "
                    "Return only valid JSON that matches the requested schema exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ]

    def _call_groq_json(self, prompt, schema_name, schema, temperature=0.1, reasoning_effort="medium"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self._groq_messages(prompt),
            "temperature": temperature,
            "response_format": build_groq_response_format(self.model, schema_name, schema),
        }

        if self.model.startswith("openai/gpt-oss-"):
            payload["reasoning_effort"] = reasoning_effort
            payload["reasoning_format"] = "hidden"

        response = requests.post(self.url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise Exception(f"Groq API Error: {response.text}")

        text = response.json()["choices"][0]["message"]["content"]
        return parse_json_text(text)

    def _call_gemini_json(self, prompt, schema, temperature=0.1):
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise Exception(f"Gemini API Error: {response.text}")

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return parse_json_text(text)

    def structure_document(self, raw_text):
        prompt = f"""
        Convert the following raw medical record into structured documentation.
        Return ONLY valid JSON that matches the schema.

        CODER-STYLE RULES:
        1. Capture the main reason for encounter in 'encounter_reason' if documented.
        2. Preserve explicit provider wording in 'provider_diagnoses_text' when present.
        3. Do not invent diagnoses or facts not supported by the document.
        4. Keep each field concise but clinically complete.

        Schema:
        {DOCUMENT_SCHEMA}

        Raw Text:
        {raw_text}
        """

        if self.provider == "groq":
            data = self._call_groq_json(
                prompt,
                schema_name="structured_document",
                schema=DOCUMENT_SCHEMA,
                temperature=0.1,
                reasoning_effort="medium",
            )
        else:
            data = self._call_gemini_json(prompt, DOCUMENT_SCHEMA, temperature=0.1)

        return normalize_document_payload(data)

    def get_structured_data(self, raw_text):
        return self.structure_document(raw_text)
