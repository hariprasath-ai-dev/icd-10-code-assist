# Research Notes

## Purpose

This project was shaped around the way U.S. ICD-10-CM coding is supposed to work in practice: review the clinical record, identify the reason for the encounter, look up the term in the Alphabetic Index, verify the code in the Tabular List, apply setting-specific rules, and only then finalize the diagnosis code set.

The backend was not built as a generic fuzzy matcher. It was reframed to follow a coder-style sequence as closely as possible within a lightweight application.

## Official research sources

These were the primary references used to design the backend logic:

1. CDC ICD-10-CM overview  
   Source: [https://www.cdc.gov/nchs/icd/icd-10-cm/](https://www.cdc.gov/nchs/icd/icd-10-cm/)  
   Why it mattered: confirms ICD-10-CM is the U.S. clinical modification used for diagnosis coding and points to the official browser, Tabular List, Index, and guidelines.

2. CMS ICD-10 resource page  
   Source: [https://www.cms.gov/medicare/coding-billing/icd-10-codes](https://www.cms.gov/medicare/coding-billing/icd-10-codes)  
   Why it mattered: this is the main CMS distribution point for current ICD-10-CM files, addenda, and official guideline PDFs.

3. FY 2026 ICD-10-CM Official Guidelines for Coding and Reporting  
   Source: [https://www.cms.gov/files/document/fy-2026-icd-10-cm-coding-guidelines.pdf](https://www.cms.gov/files/document/fy-2026-icd-10-cm-coding-guidelines.pdf)  
   Why it mattered: this was the most important design source. It guided:
   - use of the Alphabetic Index and Tabular List together
   - coding to the highest supported specificity
   - outpatient handling of uncertain diagnoses
   - inpatient handling of uncertain diagnoses
   - treatment of symptoms, history, and coexisting conditions
   - first-listed or primary diagnosis thinking

4. CDC ICD-10-CM files page  
   Source: [https://www.cdc.gov/nchs/icd/icd-10-cm/files.html](https://www.cdc.gov/nchs/icd/icd-10-cm/files.html)  
   Why it mattered: confirms the official release structure and supports using Index and Tabular datasets as the backbone of the rule engine.

5. CDC ICD classification page  
   Source: [https://www.cdc.gov/nchs/icd/index.html](https://www.cdc.gov/nchs/icd/index.html)  
   Why it mattered: helps establish the U.S. responsibility split and reinforces that ICD-CM interpretation and maintenance are governed through official public health infrastructure, not ad hoc coding tables.

## What was learned from the research

The research changed the project direction in a few important ways:

- Real coding is not "find the most similar code description."
- Coders do not stop at the first likely term; they verify in the Tabular List.
- Encounter context matters. The same phrase can be coded differently depending on whether it is confirmed, suspected, historical, symptomatic, or incidental.
- Outpatient and inpatient uncertain diagnoses must be treated differently.
- Symptoms should not always be coded separately when a more definitive diagnosis is already established and supported.
- Specificity matters. A vague parent code should lose to a supported child code.

## How the backend was built from that research

The backend was designed as a staged workflow that mirrors coder behavior.

### 1. Convert the chart into structured clinical facts

The LLM is used first to turn raw document text into a structured clinical record and then into a clinical map such as:

- encounter reason
- confirmed diagnoses
- coexisting conditions
- suspected conditions
- symptoms
- history conditions
- procedures

This step exists because the chart is messy, but the LLM is not trusted to choose the final code set by itself.

### 2. Normalize the extracted medical language

Before matching, extracted terms are cleaned and standardized:

- objects and lists from LLM JSON are flattened into usable text
- duplicates are removed
- missing categories are filled with empty defaults
- text is normalized for consistent comparison

This was added because real outputs from cloud models are not always shaped the same way.

### 3. Use the Alphabetic Index as the first lookup layer

The rule engine uses the ICD Index as the first discovery mechanism, which is much closer to how coders search than generic fuzzy matching.

The engine:

- builds searchable index records from `index.json`
- keeps primary terms and aliases
- scores term-to-index matches using overlap and exactness
- ignores weak matches below a confidence threshold

This is the "find the likely family of codes" stage.

### 4. Verify candidates against Tabular-valid codes

After candidate discovery, the engine checks codes against the loaded ICD data and keeps only codes that are valid in the current data files.

It also prefers better-supported and more specific codes by using:

- term overlap with code titles
- include-term overlap
- penalties for vague codes like unspecified or NOS when the documentation is more specific
- penalties for context words that do not fit the source term
- family cleanup so broader parent codes do not remain when a more specific child code is present

This is the "verify in the Tabular List and code to highest specificity" stage translated into software behavior.

### 5. Apply setting-aware guideline logic

The backend then applies rules based on coding guidance, especially around uncertainty and intent:

- outpatient suspected conditions are not promoted as confirmed diagnoses
- inpatient suspected conditions may be treated as established when appropriate
- history terms go to history coding buckets
- symptom terms prefer symptom chapters
- coexisting active conditions are kept with diagnoses rather than treated like history

This is where the project moved away from simple lookup and toward coding logic.

### 6. Select a primary diagnosis

The system now always attempts to identify a primary or first-listed diagnosis.

That selection uses:

- encounter reason terms first
- then confirmed diagnoses
- then coexisting conditions
- and only later symptom-based fallbacks

Within those groups, candidates are ranked with extra weight for clinically important wording and penalties for vague wording.

This was added because coders do not just output a flat list. They sequence diagnoses.

### 7. Use the LLM only as a refinement layer

After the rule engine creates an initial code set, the LLM may refine presentation and explanation, but the backend sanitizes the result again before final output.

That means:

- invalid codes are removed
- unsupported categories are ignored
- outpatient uncertainty rules are still enforced
- if refinement fails, the system falls back to the rule-based result

This keeps the LLM useful without giving it full authority over coding.

## Practical backend philosophy

The backend is built on a hybrid principle:

- LLM for chart understanding
- rules for coding control

That approach was chosen because medical coding is highly context-dependent, but also highly constrained by formal rules. A pure LLM workflow is too unstable. A pure string-matching workflow is too shallow. The current backend tries to combine the strengths of both.

## What is still not fully covered

Even after the redesign, this is still not a full production encoder. Important gaps remain:

- full parsing of `code first`
- full parsing of `use additional code`
- full `Excludes1` and `Excludes2` logic
- manifestation and etiology sequencing
- provider query workflows when documentation is ambiguous
- formal benchmark evaluation on a labeled chart dataset

Because of that, the system can be made stronger, but it should not be described as guaranteed 100% accurate.

## Summary

The backend was built from official U.S. ICD-10-CM guidance and modeled after the real coder pattern:

1. read the chart
2. identify the encounter reason and clinical facts
3. search the Index
4. verify in the Tabular List
5. apply setting-aware rules
6. choose the primary diagnosis
7. return a cleaned final code set with review flags and explanation

That research is the reason the project now behaves more like a coding workflow and less like a generic code similarity tool.
