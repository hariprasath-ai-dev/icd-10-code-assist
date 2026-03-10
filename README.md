# ICD-10-CM Coding Assistant

Streamlit app for ICD-10-CM diagnosis support using:

- Groq as the default LLM backend
- Gemini as an optional plug-in backend
- A local rule engine plus ICD-10-CM index/tabular data for candidate ranking, validation, and primary diagnosis selection

## Setup

Install dependencies:

```powershell
python -m pip install streamlit PyPDF2 python-dotenv requests
```

Create or update `.env`:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Optional: enable Gemini as a plug-in backend
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-pro

# Optional: force Gemini instead of the default Groq backend
LLM_PROVIDER=gemini
```

Default behavior:

- If `LLM_PROVIDER` is not set, the app uses Groq.
- Gemini is kept available in the backend, but it is not the default runtime path.
- If the requested provider is unavailable, the app falls back to the other supported provider.

## Run

```powershell
python -m streamlit run streamlit_app.py
```

## Project Files

- `streamlit_app.py`: Streamlit UI only
- `analysis_pipeline.py`: main analysis workflow
- `provider_config.py`: provider resolution and provider metadata
- `llm_reader.py`: structured document extraction
- `llm_interpreter.py`: clinical concept extraction, validation, and explanation
- `llm_contracts.py`: JSON schemas and normalization helpers
- `rule_engine.py`: ICD candidate ranking, validation, sequencing, and primary diagnosis logic
- `codes.json`, `index.json`, `tabular.json`, `rules.json`: local ICD-10-CM knowledge base
- `TECHNICAL_FLOW.md`: minimal technical flow documentation
- `architecture.md`: high-level backend and output flow

## Notes

- This app is designed as coding assistance, not autonomous final coding.
- Best accuracy still depends on documentation quality and the local rule layer.
- Inpatient vs outpatient logic matters and is selectable in the UI.
