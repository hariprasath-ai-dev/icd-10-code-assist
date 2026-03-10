# Architecture

## Purpose

This system helps turn a medical note into a coding-ready ICD-10-CM result.

It is designed as a hybrid workflow:

- an LLM reads and interprets the note
- the backend rule layer decides which codes are acceptable
- the final output shows the likely primary diagnosis and supporting codes

## High-Level Flow

1. A medical PDF is uploaded.
2. The note text is extracted from the PDF.
3. The LLM converts the raw note into a clean clinical summary.
4. The LLM identifies the main encounter reason, confirmed conditions, coexisting conditions, symptoms, history, and procedures.
5. The backend rule layer matches those findings against the local ICD-10-CM knowledge base.
6. The backend filters weak or invalid matches, applies setting-aware logic, and ranks the strongest coding options.
7. The backend selects the primary diagnosis or first-listed condition.
8. The system returns:
   - the primary diagnosis
   - additional validated codes
   - review warnings for low-confidence cases
   - a short clinical rationale

## Decision Logic

The backend is intentionally responsible for the final coding shape.

That means it handles:

- code ranking
- specificity checks
- outpatient vs inpatient behavior
- symptom vs diagnosis separation
- primary diagnosis selection
- low-confidence review warnings

The LLM helps understand the note, but the backend decides what is safe to keep.

## Provider Strategy

- Groq is the main runtime backend.
- Gemini remains available as a plug-in backend.
- If Gemini is explicitly requested, it can be used without changing the rest of the flow.

## Output Shape

For each chart, the system aims to produce:

- one primary diagnosis
- additional validated supporting codes
- a brief rationale
- warning signals when the documentation is not strong enough for a confident answer
