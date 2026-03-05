import streamlit as st
import os
import json
import logging
import time
from datetime import datetime
from llm_reader import LLMReader
from llm_interpreter import LLMInterpreter
from rule_engine import RuleEngine
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="ICD-10-CM Coding Assistant", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 5px; margin-bottom: 1rem; }
    .code-box { background-color: #ffffff; padding: 1.2rem; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 0.8rem; }
    .category-header { color: #495057; font-weight: bold; margin-top: 1.5rem; margin-bottom: 0.5rem; border-bottom: 2px solid #e9ecef; font-size: 1.2em; }
    </style>
""", unsafe_allow_html=True)

def process_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def main():
    st.title("🩺 ICD-10-CM Coding Assistant")
    st.sidebar.header("Control Panel")
    
    uploaded_file = st.sidebar.file_uploader("Upload Medical PDF", type="pdf")
    show_exp = st.sidebar.checkbox("Full Rational Explanation", value=True)
    
    if uploaded_file:
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("NEW ANALYSIS SESSION STARTED")
        logger.info(f"File: {uploaded_file.name}")
        
        with st.status("Analyzing Medical Record...", expanded=True) as status:
            # 1. Extraction
            st.write("📖 Reading document...")
            logger.info("Stage 1: Document extraction started")
            raw_text = process_pdf(uploaded_file)
            logger.info(f"Extracted {len(raw_text)} characters from PDF")
            
            reader = LLMReader(provider="openrouter")
            structured_doc = reader.get_structured_data(raw_text)
            logger.info("Stage 1: Document structured successfully")
            
            # 2. Interpretation
            st.write("🧠 Clinical Interpretation...")
            logger.info("Stage 2: Clinical interpretation started")
            interpreter = LLMInterpreter(provider="openrouter")
            clinical_map = interpreter.interpret_meaning(structured_doc)
            logger.info(f"Stage 2: Extracted {sum(len(v) for v in clinical_map.values())} clinical entities")
            
            # 3. Rule Engine
            st.write("⚖️ Rule-Based Mapping...")
            logger.info("Stage 3: Rule engine processing started")
            engine = RuleEngine()
            candidates = engine.discover_candidates(clinical_map)
            logger.info(f"Stage 3: Found {sum(len(v) for v in candidates.values())} candidate codes")
            
            initial_results, applied_refs = engine.enforce_guidelines(clinical_map, candidates, setting="outpatient")
            logger.info(f"Stage 3: Applied {len(applied_refs)} guideline rules")
            
            # 4. AI Refinement (Accuracy Enforcement)
            st.write("🔍 Verifying & Refining (Strict Mode)...")
            logger.info("Stage 4: AI refinement started")
            final_results = interpreter.refine_results(initial_results, clinical_map)
            logger.info(f"Stage 4: Finalized {sum(len(v) for v in final_results.values())} codes")
            
            # 5. Explanation
            st.write("📝 Formal Explanation...")
            logger.info("Stage 5: Generating explanation")
            explanation = interpreter.generate_explanation(final_results, applied_refs, clinical_map)
            logger.info("Stage 5: Explanation generated successfully")
            
            # Logging
            with open("pipeline_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- SESSION ---\nMAP: {json.dumps(clinical_map)}\nRESULTS: {json.dumps(final_results)}\n")
            
            # Calculate elapsed time
            end_time = time.time()
            elapsed_seconds = int(end_time - start_time)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            elapsed_time_str = f"{minutes:02d}:{seconds:02d}"
            
            status.update(label="Analysis Complete", state="complete", expanded=False)
            logger.info(f"ANALYSIS SESSION COMPLETED SUCCESSFULLY in {elapsed_time_str}")
            logger.info("=" * 80)
        
        # Display elapsed time
        st.success(f"✅ Analysis completed in **{elapsed_time_str}** (mm:ss)")

        # Output Display - Category Results FIRST
        st.header("📋 Analysis Results")
        
        st.divider()
        cat_list = list(final_results.items())
        
        # Display each category in its own section
        for category, codes in cat_list:
            # Filter codes to ensure they exist in database
            valid_codes = [c for c in codes if c.replace(".", "") in engine.codes]
            
            # Skip category if no valid codes
            if not valid_codes:
                logger.info(f"Category '{category}' skipped - no valid codes")
                continue
            
            st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)
            logger.info(f"Displaying category '{category}' with {len(valid_codes)} codes")

            cols = st.columns(2) 
            for idx, code in enumerate(valid_codes):
                with cols[idx % 2]:
                    clean_code = code.replace(".", "")
                    desc = engine.codes.get(clean_code, {}).get("description", "Description missing")
                    
                    # Formatting code: I7133 -> I71.33
                    display_code = clean_code
                    if len(clean_code) > 3:
                        display_code = f"{clean_code[:3]}.{clean_code[3:]}"
                        
                    st.markdown(f"""
                        <div class='code-box'>
                            <span style='font-size: 1.1em; color: #007bff;'><strong>{display_code}</strong></span><br>
                            <small style='color: #212529;'>{desc}</small>
                        </div>
                    """, unsafe_allow_html=True)

        # Output Display - Explanation NEXT
        if show_exp:
            st.divider()
            with st.expander("📝 Detailed Clinical Rationale", expanded=True):
                st.markdown(explanation)

        # Debug Data
        with st.expander("Original Extractions"):
            st.json(clinical_map)

if __name__ == "__main__":
    main()
