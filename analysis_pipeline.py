import json
import logging
from dataclasses import dataclass

from llm_interpreter import LLMInterpreter
from llm_reader import LLMReader
from rule_engine import RuleEngine


logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    structured_doc: dict
    clinical_map: dict
    candidates: dict
    initial_results: dict
    final_results: dict
    primary_diagnosis: dict | None
    review_flags: list[str]
    explanation: str
    applied_refs: list[str]


class AnalysisPipeline:
    def __init__(self, provider, setting):
        self.provider = provider
        self.setting = setting
        self.reader = LLMReader(provider=provider)
        self.interpreter = LLMInterpreter(provider=provider)
        self.engine = RuleEngine()

    def _emit(self, progress_callback, message):
        if callable(progress_callback):
            progress_callback(message)

    def run(self, raw_text, progress_callback=None):
        self._emit(progress_callback, "Reading document...")
        logger.info("Stage 1: Document extraction started")
        structured_doc = self.reader.get_structured_data(raw_text)
        logger.info("Stage 1: Document structured successfully with %s", self.provider)

        self._emit(progress_callback, "Clinical interpretation...")
        logger.info("Stage 2: Clinical interpretation started")
        clinical_map = self.interpreter.interpret_meaning(structured_doc)
        clinical_map = self.engine.canonicalize_clinical_map(clinical_map)
        logger.info(
            "Stage 2: Extracted %s clinical entities with %s",
            sum(len(values) for values in clinical_map.values()),
            self.provider,
        )

        self._emit(progress_callback, "Rule-based mapping...")
        logger.info("Stage 3: Rule engine processing started")
        candidates = self.engine.discover_candidates(clinical_map)
        logger.info("Stage 3: Found %s candidate codes", sum(len(values) for values in candidates.values()))

        initial_results, applied_refs = self.engine.enforce_guidelines(
            clinical_map,
            candidates,
            setting=self.setting,
        )
        logger.info("Stage 3: Applied %s guideline rules", len(applied_refs))

        self._emit(progress_callback, "Verifying and refining...")
        logger.info("Stage 4: AI refinement started")
        try:
            refined_results = self.interpreter.refine_results(initial_results, clinical_map)
            logger.info(
                "Stage 4: Finalized %s codes with %s",
                sum(len(values) for values in refined_results.values()),
                self.provider,
            )
        except Exception as exc:
            logger.warning("Stage 4 refinement failed with %s: %s", self.provider, exc)
            refined_results = initial_results

        final_results = self.engine.finalize_results(
            refined_results,
            initial_results,
            setting=self.setting,
        )
        primary_diagnosis = self.engine.select_primary_diagnosis(final_results, clinical_map)
        if primary_diagnosis and "Diagnoses" in final_results:
            final_results["Diagnoses"] = [primary_diagnosis["code"]] + [
                code for code in final_results["Diagnoses"] if code != primary_diagnosis["code"]
            ]
        review_flags = self.engine.get_review_flags(final_results, clinical_map)

        self._emit(progress_callback, "Generating explanation...")
        logger.info("Stage 5: Generating explanation")
        try:
            explanation = self.interpreter.generate_explanation(final_results, applied_refs, clinical_map)
            logger.info("Stage 5: Explanation generated successfully with %s", self.provider)
        except Exception as exc:
            logger.warning("Stage 5 explanation failed with %s: %s", self.provider, exc)
            explanation = "Unable to generate explanation at this time."

        with open("pipeline_debug.log", "a", encoding="utf-8") as handle:
            handle.write(
                "\n--- SESSION ---\n"
                f"PROVIDER: {self.provider}\n"
                f"MAP: {json.dumps(clinical_map)}\n"
                f"RESULTS: {json.dumps(final_results)}\n"
            )

        return AnalysisResult(
            structured_doc=structured_doc,
            clinical_map=clinical_map,
            candidates=candidates,
            initial_results=initial_results,
            final_results=final_results,
            primary_diagnosis=primary_diagnosis,
            review_flags=review_flags,
            explanation=explanation,
            applied_refs=applied_refs,
        )
