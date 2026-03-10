import json
import logging
import os

import requests
from dotenv import load_dotenv

from llm_contracts import (
    CLINICAL_MAP_SCHEMA,
    RESULTS_SCHEMA,
    build_groq_response_format,
    normalize_clinical_map,
    normalize_results_payload,
    parse_json_text,
)
from provider_config import get_provider_model

load_dotenv()

logger = logging.getLogger(__name__)


class LLMInterpreter:
    def __init__(self, provider="gemini"):
        """
        Initialize LLM Interpreter with specified provider.

        Args:
            provider: "gemini" or "groq"
        """
        self.provider = provider

        if provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY")
            self.url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = get_provider_model("groq")
            logger.info("LLMInterpreter initialized with Groq model: %s", self.model)
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.model = get_provider_model("gemini")
            self.url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                f"?key={self.api_key}"
            )
            logger.info("LLMInterpreter initialized with Gemini model: %s", self.model)

    def _groq_messages(self, prompt, system_instruction):
        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

    def _call_groq_json(
        self,
        prompt,
        schema_name,
        schema,
        system_instruction,
        temperature=0.1,
        reasoning_effort="high",
    ):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self._groq_messages(prompt, system_instruction),
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

    def _call_groq_text(self, prompt, system_instruction, temperature=0.3, reasoning_effort="medium"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self._groq_messages(prompt, system_instruction),
            "temperature": temperature,
        }

        if self.model.startswith("openai/gpt-oss-"):
            payload["reasoning_effort"] = reasoning_effort

        response = requests.post(self.url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise Exception(f"Groq API Error: {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def _call_gemini_text(self, prompt, temperature=0.3):
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise Exception(f"Gemini API Error: {response.text}")

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def interpret_meaning(self, structured_doc):
        prompt = f"""
        Extract coding-relevant clinical concepts from the medical record.
        Return ONLY valid JSON that matches the schema.

        CODER-STYLE RULES:
        1. Put the condition, problem, or symptom chiefly responsible for the encounter into 'encounter_reason'.
        2. Put only confirmed active conditions into 'confirmed_diagnoses'.
        3. Put chronic or active comorbidities that affect current care into 'coexisting_conditions'.
        4. Put uncertain, suspected, rule-out, possible, compatible with, or working diagnoses into 'suspected_conditions'.
        5. Put only genuine symptoms/signs into 'symptoms'. Do not duplicate a symptom as a confirmed diagnosis.
        6. Put resolved history, status, or past conditions that are not active this encounter into 'history_conditions'.
        7. Put all procedures, imaging, surgeries, and interventions into 'procedures'.
        8. Use standard clinical names only. No ICD codes.
        9. Do not invent findings not documented in the note.

        Structured Doc:
        {json.dumps(structured_doc)}
        """

        system_instruction = (
            "You are a clinical coding extraction assistant. "
            "Return only valid JSON that matches the requested schema exactly."
        )

        if self.provider == "groq":
            data = self._call_groq_json(
                prompt,
                schema_name="clinical_map",
                schema=CLINICAL_MAP_SCHEMA,
                system_instruction=system_instruction,
                temperature=0.1,
                reasoning_effort="high",
            )
        else:
            data = self._call_gemini_json(prompt, CLINICAL_MAP_SCHEMA, temperature=0.1)

        return normalize_clinical_map(data)

    def generate_explanation(self, codes_by_category, applied_refs, clinical_map):
        prompt = f"""
        Generate a concise clinical rationale for these code assignments.

        Assigned Codes: {json.dumps(codes_by_category)}
        Clinical Findings: {json.dumps(clinical_map)}
        Applied References: {json.dumps(applied_refs)}

        INSTRUCTIONS:
        - Link each code category to specific findings in the medical record.
        - Explain why the first-listed diagnosis was selected if one exists.
        - Focus only on why codes were selected based on documentation.
        - Be concise and professional.
        - Do not discuss codes that were not assigned.
        """

        system_instruction = "You are a medical coding explanation assistant."
        if self.provider == "groq":
            return self._call_groq_text(
                prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                reasoning_effort="medium",
            )
        return self._call_gemini_text(prompt, temperature=0.3)

    def refine_results(self, initial_results, clinical_map):
        prompt = f"""
        STRICT VALIDATION of ICD-10-CM assignments.

        Initial Assignment: {json.dumps(initial_results)}
        Clinical Data: {json.dumps(clinical_map)}

        VALIDATION RULES:
        1. Keep only codes explicitly supported by the documented findings.
        2. Remove codes that rely on missing details, unsupported specificity, or wrong context.
        3. Do not keep routine integral symptoms when a confirmed diagnosis fully explains them, unless they appear separately evaluated or clearly not integral.
        4. For outpatient logic, uncertain diagnoses should remain in 'Suspected Conditions' or be removed if unsupported.
        5. Use only these categories: "Diagnoses", "Suspected Conditions", "Symptoms", "Signs", "History", "Procedures/Imaging".
        6. Return only valid JSON matching the schema.
        """

        system_instruction = (
            "You are a medical coding validation assistant. "
            "Return only valid JSON that matches the requested schema exactly."
        )

        if self.provider == "groq":
            data = self._call_groq_json(
                prompt,
                schema_name="validated_results",
                schema=RESULTS_SCHEMA,
                system_instruction=system_instruction,
                temperature=0.1,
                reasoning_effort="high",
            )
        else:
            data = self._call_gemini_json(prompt, RESULTS_SCHEMA, temperature=0.1)

        return normalize_results_payload(data)
