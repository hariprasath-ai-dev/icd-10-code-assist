import os

import requests


DEFAULT_PROVIDER = "groq"
SUPPORTED_PROVIDERS = ("groq", "gemini")
LEGACY_GROQ_MODELS = {"llama-3.1-8b-instant"}
LEGACY_GEMINI_MODELS = {"gemini-2.0-flash", "gemini-flash-latest"}


def get_provider_model(provider):
    if provider == "gemini":
        configured = os.getenv("GEMINI_MODEL", "").strip()
        if not configured or configured in LEGACY_GEMINI_MODELS:
            return "gemini-2.5-pro"
        return configured

    configured = os.getenv("GROQ_MODEL", "").strip()
    if not configured or configured in LEGACY_GROQ_MODELS:
        return "openai/gpt-oss-120b"
    return configured


def provider_is_available(provider):
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))

    api_key = os.getenv("GROQ_API_KEY")
    model_name = get_provider_model("groq")
    if not api_key:
        return False

    try:
        response = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5,
        )
        if response.status_code != 200:
            return False
        model_ids = {item.get("id") for item in response.json().get("data", []) if item.get("id")}
        return model_name in model_ids or not model_ids
    except Exception:
        return False


def resolve_provider():
    requested = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    if requested not in SUPPORTED_PROVIDERS:
        requested = DEFAULT_PROVIDER

    provider_order = [requested] + [provider for provider in SUPPORTED_PROVIDERS if provider != requested]
    for provider in provider_order:
        if provider_is_available(provider):
            return provider

    raise RuntimeError("No provider found. Configure GROQ_API_KEY or GEMINI_API_KEY.")


def get_provider_label(provider):
    if provider == "gemini":
        return f"Gemini ({get_provider_model('gemini')})"
    return f"Groq ({get_provider_model('groq')})"
