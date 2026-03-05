# ICD-10-CM Coding Assistant (Hybrid AI/Rule Engine)

A robust medical coding assistant that combines the clinical reasoning of LLMs with a deterministic Rule Engine for accurate ICD-10-CM assignment.

## 🚀 How to Run

1.  **Install Dependencies**:
    ```powershell
    python -m pip install streamlit PyPDF2 python-dotenv requests
    ```

2.  **Configure API Keys**:
    *   Open the `.env` file.
    *   Add your Gemini API Key: `GEMINI_API_KEY=your_key_here`
    *   Add your OpenRouter API Key: `OPEN_ROUTER_KEY=your_key_here`
    *   Set OpenRouter Model: `OPENROUTER_MODEL=qwen/qwen3-235b-a22b-thinking-2507`
    *   Note: You can change the model by updating `OPENROUTER_MODEL` to any free OpenRouter model

3.  **Launch the App**:
    ```powershell
    python -m streamlit run streamlit_app.py
    ```

4.  **Select Provider**:
    *   In the sidebar, choose between "OpenRouter (Gemini 2.0 Flash)" or "Google Gemini Direct"
    *   OpenRouter provides access to multiple models through a unified API

## 🛠️ How It Works

The system follows a strict multi-stage pipeline to ensure clinical accuracy and regulatory compliance:

1.  **Stage 1: LLM Reader**: Extracts raw text from the uploaded PDF and structures it into clinical sections (Chief Complaint, Labs, Assessment, Plan). Supports both Google Gemini and OpenRouter providers.
2.  **Stage 2: LLM Interpreter**: Analyzes the structured data to identify confirmed diagnoses, suspected conditions, symptoms, and medical history. It uses clinical reasoning to distinguish "Active" conditions from historical notes.
3.  **Stage 3: Rule Engine (Deterministic)**: 
    *   **Candidate Discovery**: Performs fuzzy keyword matching against a local JSON index of the official ICD-10-CM Alphabetic Index.
    *   **Severity Re-ranking**: Automatically prioritizes acute, ruptured, or malignant conditions as the **Primary Diagnosis**.
    *   **Guideline Enforcement**: Applies official ICD-10-CM guidelines (e.g., coding uncertain diagnoses for inpatients, excluding integral symptoms) using a deterministic logic layer.
4.  **Stage 4: Narrative Explanation**: The LLM generates a clear, human-readable justification for every code assigned, referencing specific parts of the medical record.

## 🔌 LLM Provider Options

### OpenRouter (Recommended)
*   **Model**: Configurable via `OPENROUTER_MODEL` environment variable
*   **Default**: `qwen/qwen3-235b-a22b-thinking-2507`
*   **Context**: 262,000 tokens
*   **Benefits**: Advanced reasoning model with thinking capabilities, easily switch models
*   **Setup**: 
    - Add `OPEN_ROUTER_KEY` to `.env` file
    - Set `OPENROUTER_MODEL` to your preferred model ID
*   **Available Free Models**: See list below

### Google Gemini Direct
*   **Model**: `gemini-2.0-flash`
*   **Benefits**: Direct access to Google's API
*   **Setup**: Add `GEMINI_API_KEY` to `.env` file

### How to Change OpenRouter Model
Simply update the `OPENROUTER_MODEL` variable in `.env`:
```env
# Example: Switch to Llama 3.3 70B
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Example: Switch to Gemini via OpenRouter
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Example: Switch to Mistral Small
OPENROUTER_MODEL=mistralai/mistral-small-3.1:free
```

## 📁 Project Structure

*   `streamlit_app.py`: The user interface and pipeline orchestrator.
*   `llm_reader.py`: Handles document extraction and structuring.
*   `llm_interpreter.py`: Clinical entity extraction and interpretation.
*   `rule_engine.py`: The deterministic logic core with re-ranking and guideline rules.
*   `process_icd.py`: Utility script to rebuild the local knowledge bases from raw XML data.
*   `codes.json`, `index.json`, `tabular.json`: The localized ICD-10-CM knowledge base (2026 Edition).

**Note**: Currently supports ICD-10-CM (diagnosis) codes. ICD-10-PCS (procedure) codes can be added by including a PCS dataset.
