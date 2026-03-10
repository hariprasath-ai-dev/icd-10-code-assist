import time

import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv

from analysis_pipeline import AnalysisPipeline
from app_logging import configure_logging
from provider_config import get_provider_label, resolve_provider

load_dotenv()
logger = configure_logging()

st.set_page_config(page_title="ICD-10-CM Coding Assistant", layout="wide")

st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 5px; margin-bottom: 1rem; }
    .code-box { background-color: #ffffff; padding: 1.2rem; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 0.8rem; }
    .category-header { color: #495057; font-weight: bold; margin-top: 1.5rem; margin-bottom: 0.5rem; border-bottom: 2px solid #e9ecef; font-size: 1.2em; }
    </style>
    """,
    unsafe_allow_html=True,
)


def process_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def render_code_box(code, description, subtitle=None):
    display_code = code
    if len(display_code) > 3:
        display_code = f"{display_code[:3]}.{display_code[3:]}"

    subtitle_html = ""
    if subtitle:
        subtitle_html = f"<br><small style='color: #6c757d;'>{subtitle}</small>"

    st.markdown(
        f"""
        <div class='code-box'>
            <span style='font-size: 1.1em; color: #007bff;'><strong>{display_code}</strong></span><br>
            <small style='color: #212529;'>{description}</small>{subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.title("ICD-10-CM Coding Assistant")
    st.sidebar.header("Control Panel")

    try:
        provider = resolve_provider()
    except RuntimeError as exc:
        st.sidebar.error(str(exc))
        st.stop()

    st.sidebar.success(f"Active backend: {get_provider_label(provider)}")
    st.sidebar.caption("Groq is the default runtime backend. Gemini stays available as a plug-in backend via `LLM_PROVIDER=gemini`.")

    uploaded_file = st.sidebar.file_uploader("Upload Medical PDF", type="pdf")
    encounter_setting = st.sidebar.selectbox("Coding Setting", options=["Outpatient", "Inpatient"], index=0)
    setting = encounter_setting.lower()
    show_explanation = st.sidebar.checkbox("Full Rational Explanation", value=True)

    if not uploaded_file:
        return

    start_time = time.time()
    logger.info("=" * 80)
    logger.info("NEW ANALYSIS SESSION STARTED")
    logger.info("Provider: %s", provider)
    logger.info("File: %s", uploaded_file.name)

    raw_text = process_pdf(uploaded_file)
    logger.info("Extracted %s characters from PDF", len(raw_text))

    pipeline = AnalysisPipeline(provider=provider, setting=setting)

    with st.status("Analyzing Medical Record...", expanded=True) as status:
        try:
            result = pipeline.run(raw_text, progress_callback=st.write)
        except Exception as exc:
            logger.exception("Analysis failed")
            st.error(f"Analysis failed: {exc}")
            return
        status.update(label="Analysis Complete", state="complete", expanded=False)

    elapsed_seconds = int(time.time() - start_time)
    elapsed_time = f"{elapsed_seconds // 60:02d}:{elapsed_seconds % 60:02d}"
    logger.info("ANALYSIS SESSION COMPLETED SUCCESSFULLY in %s", elapsed_time)
    logger.info("=" * 80)

    st.success(f"Analysis completed in {elapsed_time} (mm:ss)")
    st.header("Analysis Results")

    if result.primary_diagnosis:
        render_code_box(
            result.primary_diagnosis["code"],
            result.primary_diagnosis["description"],
            subtitle=f"Primary diagnosis based on documented term: {result.primary_diagnosis['term']}",
        )

    for flag in result.review_flags:
        st.warning(flag)

    st.divider()
    for category, codes in result.final_results.items():
        valid_codes = [code for code in codes if pipeline.engine.is_valid_code(code)]
        if not valid_codes:
            logger.info("Category '%s' skipped - no valid codes", category)
            continue

        st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)
        logger.info("Displaying category '%s' with %s codes", category, len(valid_codes))

        cols = st.columns(2)
        for idx, code in enumerate(valid_codes):
            with cols[idx % 2]:
                render_code_box(code, pipeline.engine.get_code_description(code))

    if show_explanation:
        st.divider()
        with st.expander("Detailed Clinical Rationale", expanded=True):
            st.markdown(result.explanation)

    with st.expander("Original Extractions"):
        st.json(result.clinical_map)


if __name__ == "__main__":
    main()
