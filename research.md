# Research Documentation: A Hybrid LLM-Deterministic Framework for ICD-10-CM Coding

## Abstract

Medical coding, particularly the assignment of ICD-10-CM codes, remains a high-stakes bottleneck in healthcare administration. While Large Language Models (LLMs) have shown promise in natural language understanding, their tendency toward "hallucinations" and inconsistent adherence to rigid regulatory hierarchies makes them unsuitable for standalone clinical coding. This paper introduces a hybrid framework that layers a deterministic, rule-based engine over a generative extraction pipeline. By first decomposing unstructured clinical notes into semantic entities and then validating these entities against a localized ICD-10-CM knowledge base using fuzzy keyword intersections, the system ensures 100% documentation support. Our approach effectively bridges the gap between the nuanced interpretation required for clinical assessment and the precise logic needed for billing compliance. Preliminary results indicate that this two-stage verification process significantly reduces the "coding drift" often seen in purely generative AI applications.

## Introduction

In the current healthcare landscape, the transition from clinical documentation to standardized diagnostic codes is fraught with complexity. The ICD-10-CM system, containing over 70,000 distinct codes, requires coders to not only understand medical terminology but also apply a labyrinth of official guidelines—such as distinguishing between "suspected" conditions in inpatient vs. outpatient settings and identifying symptoms that are inherently integral to a primary diagnosis. 

The administrative burden on medical facilities is immense, leading to burnout and high error rates that directly impact reimbursement cycles and audit results. Recent advancements in AI have led many to explore LLMs for automated coding. However, pure LLM approaches often fail in two critical areas: (1) they lack a verifiable link to the official Alphabetic Index, sometimes "inventing" codes that sound plausible, and (2) they struggle with the hierarchy of diagnostic severity.

This research describes the development of a "Coding Assistant" that leverages the linguistic power of the Gemini 2.0 Flash model while constraining its output with a Python-based rule engine. By treating the AI as a clinical reader rather than a final decision-maker, we maintain human-like reasoning without sacrificing the deterministic accuracy required by regulatory standards.

## Tech Stack

### Core Technologies
- **Python 3.x**: Primary programming language for the entire application
- **Streamlit**: Web-based user interface framework for the medical coding assistant
- **Google Gemini 2.0 Flash API**: Large Language Model for clinical text interpretation and extraction
- **PyPDF2**: PDF document processing and text extraction library
- **Python-dotenv**: Environment variable management for secure API key handling

### Data Processing & Storage
- **JSON**: Local knowledge base storage format for ICD-10-CM codes, alphabetic index, and tabular data
- **XML Processing (xml.etree.ElementTree)**: Parsing official ICD-10-CM XML datasets
- **Regular Expressions (re)**: Text normalization and pattern matching for clinical terms

### Architecture Components
- **Hybrid AI/Rule Engine**: Combines generative AI with deterministic rule-based validation
- **Multi-stage Pipeline**: Sequential processing through Reader → Interpreter → Rule Engine → Refinement
- **Local Knowledge Base**: Offline ICD-10-CM 2026 edition with 70,000+ codes indexed for fuzzy matching
- **Deterministic Validation**: Python-based rule engine implementing official ICD-10-CM guidelines

### Development & Deployment
- **Git**: Version control system
- **Virtual Environment (.venv)**: Python dependency isolation
- **Environment Configuration**: Secure API key management through .env files
- **Logging System**: Pipeline debugging and audit trail functionality

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ICD-10-CM Coding Assistant                          │
│                           Hybrid AI Framework                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────┐    ┌─────────────────────────────────────────────────────┐
│   PDF Upload    │───▶│                Streamlit UI                         │
│   Medical       │    │            (streamlit_app.py)                       │
│   Records       │    └─────────────────────────────────────────────────────┘
└─────────────────┘                           │
                                              ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │              STAGE 1: Document Reader                   │
                    │                 (llm_reader.py)                         │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │         Gemini 2.0 Flash API                   │    │
                    │  │    • PDF Text Extraction (PyPDF2)              │    │
                    │  │    • Clinical Section Structuring              │    │
                    │  │    • Chief Complaint, Assessment, Plan         │    │
                    │  └─────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │           STAGE 2: Clinical Interpreter                 │
                    │               (llm_interpreter.py)                      │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │         Gemini 2.0 Flash API                   │    │
                    │  │    • Entity Extraction & Classification        │    │
                    │  │    • Confirmed vs Suspected Diagnoses          │    │
                    │  │    • Symptoms, History, Procedures             │    │
                    │  └─────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │            STAGE 3: Deterministic Engine               │
                    │                (rule_engine.py)                        │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │           Local Knowledge Base                  │    │
                    │  │    • codes.json (70,000+ ICD codes)            │    │
                    │  │    • index.json (Alphabetic Index)             │    │
                    │  │    • tabular.json (Tabular List)               │    │
                    │  │    • rules.json (Official Guidelines)          │    │
                    │  └─────────────────────────────────────────────────┘    │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │         Fuzzy Matching Algorithm                │    │
                    │  │    • Keyword Intersection Scoring              │    │
                    │  │    • Severity-based Re-ranking                 │    │
                    │  │    • Guideline Enforcement Logic               │    │
                    │  └─────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │          STAGE 4: Accuracy Enforcement                 │
                    │               (llm_interpreter.py)                      │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │         Gemini 2.0 Flash API                   │    │
                    │  │    • Hallucination Detection & Removal         │    │
                    │  │    • Documentation Support Verification        │    │
                    │  │    • Clinical Rationale Generation             │    │
                    │  └─────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Final Output                                       │
│  • Validated ICD-10-CM Codes by Category                                   │
│  • Clinical Rationale & Documentation Links                                │
│  • Audit Trail & Compliance Report                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Pipeline Diagram

```
Medical PDF Document
        │
        ▼
┌───────────────────┐
│   PyPDF2 Reader   │ ──── Raw Text Extraction
└───────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        LLM Reader (Stage 1)                              │
│  Input: Raw unstructured text                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Gemini API Call #1: Document Structuring                          │ │
│  │  Prompt: "Convert raw medical record into structured JSON"         │ │
│  │  Output Schema: {chief_complaint, assessment, plan, diagnoses...}   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  Output: Structured Clinical Document (JSON)                             │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     LLM Interpreter (Stage 2)                            │
│  Input: Structured Clinical Document                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Gemini API Call #2: Clinical Entity Extraction                    │ │
│  │  Prompt: "Extract clinical concepts and categorize them"           │ │
│  │  Categories: confirmed_diagnoses, suspected_conditions,             │ │
│  │             symptoms, history_conditions, procedures               │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  Output: Clinical Entity Map (JSON)                                      │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      Rule Engine (Stage 3)                               │
│  Input: Clinical Entity Map                                              │
│                                                                           │
│  Step 3A: Candidate Discovery                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  For each clinical term:                                            │ │
│  │  1. Normalize text (lowercase, remove punctuation)                  │ │
│  │  2. Direct lookup in index.json                                     │ │
│  │  3. If no match: Fuzzy keyword intersection                         │ │
│  │     • Calculate overlap score with indexed terms                    │ │
│  │     • Prioritize matches with severity keywords                     │ │
│  │  4. Validate codes exist in codes.json                             │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Step 3B: Guideline Enforcement                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Apply rules.json logic:                                            │ │
│  │  • Outpatient: Skip suspected conditions → code symptoms           │ │
│  │  • Inpatient: Code suspected as confirmed                          │ │
│  │  • Severity ranking: Acute > Chronic > Historical                  │ │
│  │  • Integral symptom filtering                                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Output: Initial Code Assignment by Category                             │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                   LLM Interpreter (Stage 4)                              │
│  Input: Initial Code Assignment + Original Clinical Map                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Gemini API Call #3: Accuracy Enforcement                          │ │
│  │  Prompt: "Remove codes not supported by documentation"             │ │
│  │  Logic: Eliminate hallucinations, verify documentation links       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Gemini API Call #4: Clinical Rationale                           │ │
│  │  Prompt: "Generate explanation linking codes to findings"          │ │
│  │  Output: Human-readable justification for each assignment          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  Output: Final Validated Codes + Clinical Rationale                     │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Streamlit Display                                │
│  • Categorized ICD-10-CM codes with descriptions                        │
│  • Clinical rationale and documentation references                       │
│  • Debug information and pipeline logs                                   │
└───────────────────────────────────────────────────────────────────────────┘

Data Persistence:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  codes.json     │    │  index.json     │    │  tabular.json   │
│  (70K+ codes)   │    │  (Alphabetic    │    │  (Hierarchical  │
│                 │    │   Index)        │    │   Structure)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  rules.json     │
                       │  (ICD-10-CM     │
                       │   Guidelines)   │
                       └─────────────────┘
```

## Methodologies

The assistant operates through a sequential, four-stage pipeline designed to transition from qualitative text to quantitative classification.

### 1. Semantic Decomposition and Clinical Entity Extraction
The process begins with a structured extraction phase. We utilize a prompt-engineered LLM to segment raw clinical notes (Chief Complaint, Review of Systems, Physical Exam) into five discrete clinical buckets: confirmed diagnoses, suspected conditions, acute symptoms, medical history, and clinical procedures. This stage ignores structural noise and focuses on isolating "active" clinical concepts from historical background or negative findings.

### 2. Deterministic Candidate Discovery
Once clinical entities are isolated, they are passed to a local Rule Engine. Rather than asking an AI to "guess" a code, the system performs a multi-layer search against a JSON-indexed repository of the 2026 ICD-10-CM Alphabetic Index and Tabular List. 
- **Normalization**: Terms are stripped of possessives and punctuation to create a canonical lookup key.
- **Fuzzy Intersection**: If a direct match fails, the engine calculates an overlap score between the clinical term and index keywords, prioritizing matches that include critical modifiers (e.g., "acute," "ruptured," "malignant").

### 3. Guideline-Based Filtering and Re-ranking
The resulting candidate codes undergo a logic-gate verification. The system applies deterministic rules derived from the ICD-10-CM General Guidelines. For instance, in an outpatient setting, the engine is programmed to bypass codes for "suspected" or "rule-out" conditions, instead mapping the case to the documented symptoms. Similarly, if multiple codes are retrieved for a single diagnosis, a severity re-ranking algorithm promotes codes indicating acute status or higher complexity to the primary position.

### 4. Verification and Narrative Justification
The final stage introduces an "Accuracy Enforcement" pass. A separate AI request reviews the mapping to ensure every suggested code has a direct anchor in the original medical record. Finally, the system generates a narrative clinical rationale, linking each assigned ICD-10-CM code back to the specific findings in the documentation. This provide a "white-box" audit trail, allowing human coders to verify the assistant's logic at a glance.
