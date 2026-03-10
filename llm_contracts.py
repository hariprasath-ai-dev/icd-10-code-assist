import json


STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "description": "A list of concise clinical terms using standard medical naming.",
}


DOCUMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "encounter_reason": {
            "type": "string",
            "description": "The main diagnosis, problem, or reason for visit chiefly responsible for the encounter if documented.",
        },
        "chief_complaint": {
            "type": "string",
            "description": "The patient's chief complaint or presenting concern.",
        },
        "history_of_present_illness": {
            "type": "string",
            "description": "The history of present illness and relevant timeline.",
        },
        "assessment": {
            "type": "string",
            "description": "Assessment or impression section from the note.",
        },
        "plan": {
            "type": "string",
            "description": "Plan, treatment, orders, and follow-up.",
        },
        "provider_diagnoses_text": {
            "type": "string",
            "description": "Explicit provider diagnoses or impressions copied from the record.",
        },
        "other_notes": {
            "type": "string",
            "description": "Other clinically relevant details not captured above.",
        },
    },
    "required": [
        "encounter_reason",
        "chief_complaint",
        "history_of_present_illness",
        "assessment",
        "plan",
        "provider_diagnoses_text",
        "other_notes",
    ],
}


CLINICAL_MAP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "encounter_reason": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One or more concise terms for the condition, problem, or symptom chiefly responsible for the encounter.",
            "maxItems": 3,
        },
        "confirmed_diagnoses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Confirmed active diagnoses documented by the provider.",
        },
        "coexisting_conditions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Coexisting chronic or active conditions that affect current care, treatment, or management.",
        },
        "suspected_conditions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Uncertain, suspected, possible, rule-out, or working diagnoses.",
        },
        "symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Signs or symptoms supported by the encounter documentation.",
        },
        "history_conditions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Past history, status, or resolved conditions that are not active coexisting diseases for this encounter.",
        },
        "procedures": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Procedures, imaging, surgeries, or interventions documented in the encounter.",
        },
    },
    "required": [
        "encounter_reason",
        "confirmed_diagnoses",
        "coexisting_conditions",
        "suspected_conditions",
        "symptoms",
        "history_conditions",
        "procedures",
    ],
}


RESULTS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "Diagnoses": STRING_ARRAY_SCHEMA,
        "Suspected Conditions": STRING_ARRAY_SCHEMA,
        "Symptoms": STRING_ARRAY_SCHEMA,
        "Signs": STRING_ARRAY_SCHEMA,
        "History": STRING_ARRAY_SCHEMA,
        "Procedures/Imaging": STRING_ARRAY_SCHEMA,
    },
    "required": [
        "Diagnoses",
        "Suspected Conditions",
        "Symptoms",
        "Signs",
        "History",
        "Procedures/Imaging",
    ],
}


GROQ_STRICT_JSON_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
}

GROQ_BEST_EFFORT_JSON_SCHEMA_MODELS = GROQ_STRICT_JSON_SCHEMA_MODELS | {
    "openai/gpt-oss-safeguard-20b",
    "moonshotai/kimi-k2-instruct-0905",
    "meta-llama/llama-4-scout-17b-16e-instruct",
}


def strip_json_fences(text):
    if not isinstance(text, str):
        return ""
    return text.replace("```json", "").replace("```", "").strip()


def parse_json_text(text):
    return json.loads(strip_json_fences(text))


def normalize_string(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def normalize_string_list(values):
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]

    cleaned = []
    seen = set()
    for value in values:
        if isinstance(value, dict):
            for candidate in value.values():
                if isinstance(candidate, str) and candidate.strip():
                    value = candidate
                    break
            else:
                continue
        elif isinstance(value, list):
            value = " ".join(normalize_string(item) for item in value if normalize_string(item))

        text = normalize_string(value)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def normalize_document_payload(data):
    return {
        "encounter_reason": normalize_string(data.get("encounter_reason")),
        "chief_complaint": normalize_string(data.get("chief_complaint")),
        "history_of_present_illness": normalize_string(data.get("history_of_present_illness")),
        "assessment": normalize_string(data.get("assessment")),
        "plan": normalize_string(data.get("plan")),
        "provider_diagnoses_text": normalize_string(data.get("provider_diagnoses_text")),
        "other_notes": normalize_string(data.get("other_notes")),
    }


def normalize_clinical_map(data):
    return {
        "encounter_reason": normalize_string_list(data.get("encounter_reason", [])),
        "confirmed_diagnoses": normalize_string_list(data.get("confirmed_diagnoses", [])),
        "coexisting_conditions": normalize_string_list(data.get("coexisting_conditions", [])),
        "suspected_conditions": normalize_string_list(data.get("suspected_conditions", [])),
        "symptoms": normalize_string_list(data.get("symptoms", [])),
        "history_conditions": normalize_string_list(data.get("history_conditions", [])),
        "procedures": normalize_string_list(data.get("procedures", [])),
    }


def normalize_results_payload(data):
    return {
        "Diagnoses": normalize_string_list(data.get("Diagnoses", [])),
        "Suspected Conditions": normalize_string_list(data.get("Suspected Conditions", [])),
        "Symptoms": normalize_string_list(data.get("Symptoms", [])),
        "Signs": normalize_string_list(data.get("Signs", [])),
        "History": normalize_string_list(data.get("History", [])),
        "Procedures/Imaging": normalize_string_list(data.get("Procedures/Imaging", [])),
    }


def build_groq_response_format(model, schema_name, schema):
    if model in GROQ_STRICT_JSON_SCHEMA_MODELS:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }

    if model in GROQ_BEST_EFFORT_JSON_SCHEMA_MODELS:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": False,
                "schema": schema,
            },
        }

    return {"type": "json_object"}
