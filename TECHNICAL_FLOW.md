# Technical Flow

## Runtime flow

1. `streamlit_app.py` reads the PDF and resolves the active backend.
2. `analysis_pipeline.py` runs the analysis stages.
3. `llm_reader.py` converts raw note text into a structured JSON document.
4. `llm_interpreter.py` extracts coding-relevant categories:
   - encounter reason
   - confirmed diagnoses
   - coexisting conditions
   - suspected conditions
   - symptoms
   - history conditions
   - procedures
5. `rule_engine.py` ranks ICD-10-CM candidates from the local Alphabetic Index and validates them against the local Tabular data.
6. The rule engine applies setting-aware logic:
   - outpatient uncertain diagnoses are not coded as confirmed
   - inpatient uncertain diagnoses may move into diagnoses
7. The engine sanitizes results, selects the primary diagnosis, and emits review flags for low-confidence cases.
8. `llm_interpreter.py` writes the final explanation text.

## Provider flow

- Groq is the default backend.
- Gemini stays available as a plug-in backend.
- `LLM_PROVIDER=gemini` forces Gemini.
- If the requested provider is unavailable, the app falls back to the other supported provider.

## Why the backend matters

The LLM is used for extraction and validation, but the backend rule layer is responsible for:

- candidate ranking
- code validity checks
- outpatient vs inpatient behavior
- primary diagnosis selection
- low-confidence review flags

This is what keeps the system closer to a real coder workflow than simple fuzzy matching.
