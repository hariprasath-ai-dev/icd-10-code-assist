# ICD-10-CM Coding Assistant (Hybrid AI/Rule Engine)

A robust medical coding assistant that combines the clinical reasoning of LLMs with a deterministic Rule Engine for accurate ICD-10-CM assignment.

## 🚀 How to Run

1.  **Install Dependencies**:
    ```powershell
    python -m pip install streamlit PyPDF2 python-dotenv requests
    ```

2.  **Configure API Key**:
    *   Open the `.env` file.
    *   Add your Gemini API Key: `GEMINI_API_KEY=your_key_here`

3.  **Launch the App**:
    ```powershell
    python -m streamlit run streamlit_app.py
    ```

## 🛠️ How It Works

The system follows a strict multi-stage pipeline to ensure clinical accuracy and regulatory compliance:

1.  **Stage 1: LLM Reader**: Extracts raw text from the uploaded PDF and structures it into clinical sections (Chief Complaint, Labs, Assessment, Plan).
2.  **Stage 2: LLM Interpreter**: Analyzes the structured data to identify confirmed diagnoses, suspected conditions, symptoms, and medical history. It uses clinical reasoning to distinguish "Active" conditions from historical notes.
3.  **Stage 3: Rule Engine (Deterministic)**: 
    *   **Candidate Discovery**: Performs fuzzy keyword matching against a local JSON index of the official ICD-10-CM Alphabetic Index.
    *   **Severity Re-ranking**: Automatically prioritizes acute, ruptured, or malignant conditions as the **Primary Diagnosis**.
    *   **Guideline Enforcement**: Applies official ICD-10-CM guidelines (e.g., coding uncertain diagnoses for inpatients, excluding integral symptoms) using a deterministic logic layer.
4.  **Stage 4: Narrative Explanation**: The LLM generates a clear, human-readable justification for every code assigned, referencing specific parts of the medical record.

## 📁 Project Structure

*   `streamlit_app.py`: The user interface and pipeline orchestrator.
*   `llm_reader.py`: Handles document extraction and structuring.
*   `llm_interpreter.py`: Clinical entity extraction and interpretation.
*   `rule_engine.py`: The deterministic logic core with re-ranking and guideline rules.
*   `process_icd.py`: Utility script to rebuild the local knowledge bases from raw XML data.
*   `codes.json`, `index.json`, `tabular.json`: The localized ICD-10-CM knowledge base (2026 Edition).
