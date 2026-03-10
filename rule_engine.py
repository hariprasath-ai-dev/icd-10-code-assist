import json
import re


class RuleEngine:
    def __init__(self):
        with open("codes.json", encoding="utf-8") as f:
            self.codes = json.load(f)["codes"]
        with open("index.json", encoding="utf-8") as f:
            self.index = json.load(f)["terms"]
        with open("tabular.json", encoding="utf-8") as f:
            self.tabular = json.load(f)["codes"]
        with open("rules.json", encoding="utf-8") as f:
            self.rules = json.load(f)["rules"]

        self.valid_codes = set(self.codes) | set(self.tabular)
        self.index_records = self._build_index_records()
        self.code_metadata = self._build_code_metadata()
        self.last_term_candidates = {}

    def _build_index_records(self):
        records = []
        for primary_term, entry in self.index.items():
            raw_codes = entry.get("codes", [])
            codes = [self.clean_code(code) for code in raw_codes if self.is_valid_code(code)]
            if not codes:
                continue

            variants = [primary_term] + entry.get("aliases", [])
            deduped_variants = []
            seen = set()
            for variant in variants:
                norm_variant = self.normalize(variant)
                if not norm_variant or norm_variant in seen:
                    continue
                seen.add(norm_variant)
                deduped_variants.append(norm_variant)

            records.append(
                {
                    "primary_term": primary_term,
                    "variants": deduped_variants,
                    "variant_word_sets": [set(variant.split()) for variant in deduped_variants],
                    "codes": codes,
                }
            )
        return records

    def _build_code_metadata(self):
        metadata = {}
        for code in self.valid_codes:
            title = self.get_code_description(code)
            includes = self.tabular.get(code, {}).get("includes", [])
            metadata[code] = {
                "title": title,
                "title_norm": self.normalize(title),
                "title_words": set(self.normalize(title).split()),
                "include_words": set(
                    self.normalize(" ".join(item for item in includes if isinstance(item, str))).split()
                ),
            }
        return metadata

    def clean_code(self, code):
        if not code:
            return ""
        return code.replace(".", "").strip()

    def is_valid_code(self, code):
        return self.clean_code(code) in self.valid_codes

    def get_code_description(self, code):
        clean_code = self.clean_code(code)
        if clean_code in self.codes:
            return self.codes[clean_code].get("description", clean_code)
        if clean_code in self.tabular:
            return self.tabular[clean_code].get("title", clean_code)
        return clean_code

    def normalize(self, text):
        if not isinstance(text, str):
            text = self.extract_term_text(text)
        if not text:
            return ""
        text = text.lower()
        text = text.replace("'", "")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split()).strip()

    def extract_term_text(self, term):
        if isinstance(term, str):
            return term.strip()

        if isinstance(term, dict):
            preferred_keys = (
                "term",
                "name",
                "diagnosis",
                "condition",
                "symptom",
                "procedure",
                "finding",
                "text",
                "value",
            )
            for key in preferred_keys:
                value = term.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            for value in term.values():
                if isinstance(value, str) and value.strip():
                    return value.strip()

            return ""

        if isinstance(term, list):
            parts = [self.extract_term_text(item) for item in term]
            return " ".join(part for part in parts if part).strip()

        return str(term).strip()

    def canonicalize_clinical_map(self, clinical_map):
        canonical_map = {}
        for category, values in clinical_map.items():
            if not isinstance(values, list):
                values = [values]

            cleaned_terms = []
            seen = set()
            for value in values:
                text = self.extract_term_text(value)
                if not text:
                    continue
                key = text.casefold()
                if key in seen:
                    continue
                seen.add(key)
                cleaned_terms.append(text)

            canonical_map[category] = cleaned_terms

        for required_key in (
            "encounter_reason",
            "confirmed_diagnoses",
            "coexisting_conditions",
            "suspected_conditions",
            "symptoms",
            "history_conditions",
            "procedures",
        ):
            canonical_map.setdefault(required_key, [])

        return canonical_map

    def _term_category_pairs(self, clinical_map):
        ordered_categories = (
            ("encounter_reason", clinical_map.get("encounter_reason", [])),
            ("confirmed_diagnoses", clinical_map["confirmed_diagnoses"]),
            ("coexisting_conditions", clinical_map.get("coexisting_conditions", [])),
            ("suspected_conditions", clinical_map["suspected_conditions"]),
            ("symptoms", clinical_map["symptoms"]),
            ("history_conditions", clinical_map["history_conditions"]),
            ("procedures", clinical_map.get("procedures", [])),
        )
        for category, terms in ordered_categories:
            for term in terms:
                yield category, term

    def _base_match_score(self, term_norm, term_words, variant_norm, variant_words):
        if not term_words or not variant_words:
            return 0.0

        if term_norm == variant_norm:
            return 120.0
        if term_words == variant_words:
            return 112.0

        overlap = len(term_words.intersection(variant_words))
        if overlap == 0:
            return 0.0

        if overlap < 2 and overlap != len(term_words):
            return 0.0

        score = (overlap / len(term_words)) * 65 + (overlap / len(variant_words)) * 35
        if term_words.issubset(variant_words):
            score += 8
        if variant_words.issubset(term_words):
            score += 4
        return score

    def _score_code_for_context(self, term, category, code, base_score, matched_variant_norm):
        metadata = self.code_metadata.get(code, {})
        title_words = metadata.get("title_words", set())
        include_words = metadata.get("include_words", set())
        title_norm = metadata.get("title_norm", "")

        term_norm = self.normalize(term)
        term_words = set(term_norm.split())
        matched_variant_words = set(matched_variant_norm.split())
        overlap_bonus = len(term_words.intersection(title_words)) * 6
        include_bonus = len(term_words.intersection(include_words)) * 3

        score = base_score + overlap_bonus + include_bonus
        score += min(len(code), 7) * 1.5
        score -= max(0, len(matched_variant_words) - len(term_words)) * 6
        score -= max(0, len(title_words - term_words)) * 1.5

        if "unspecified" in title_norm or "nos" in title_norm:
            vague_terms = {"nos", "unspecified", "unknown"}
            if not term_words.intersection(vague_terms):
                score -= 10

        if "other specified" in title_norm and "other" not in term_words:
            score -= 4

        contextual_words = {
            "postprocedural",
            "screening",
            "newborn",
            "pregnancy",
            "puerperium",
            "gestational",
            "pulmonary",
            "portal",
            "intracranial",
            "resistant",
            "secondary",
            "benign",
            "malignant",
        }
        unexpected_context = (matched_variant_words | title_words).intersection(contextual_words) - term_words
        score -= len(unexpected_context) * 10

        if category == "history_conditions":
            if "history" in term_norm and (code.startswith("Z") or "history" in title_norm):
                score += 10

        if category == "coexisting_conditions":
            if code.startswith("Z"):
                score -= 8
            else:
                score += 8

        if category == "symptoms":
            if code.startswith("R"):
                score += 10
            else:
                score -= 6

        if category == "procedures" and code.startswith("Z"):
            score += 4

        if "acute" in term_norm and "acute" in title_norm:
            score += 8
        if "chronic" in term_norm and "chronic" in title_norm:
            score += 8
        if "acute" in term_norm and "chronic" in title_norm:
            score -= 4
        if "chronic" in term_norm and "acute" in title_norm:
            score -= 4

        return score

    def _collapse_candidates(self, scored_candidates):
        best_by_code = {}
        for candidate in scored_candidates:
            code = candidate["code"]
            if code not in best_by_code or candidate["score"] > best_by_code[code]["score"]:
                best_by_code[code] = candidate
        return sorted(best_by_code.values(), key=lambda item: item["score"], reverse=True)

    def _drop_less_specific_family_codes(self, codes):
        cleaned_codes = []
        for code in sorted(set(codes), key=lambda item: (len(item), item)):
            more_specific_exists = any(
                other != code and other.startswith(code) and len(other) > len(code) for other in codes
            )
            if not more_specific_exists:
                cleaned_codes.append(code)
        return sorted(cleaned_codes)

    def discover_candidates(self, clinical_map):
        clinical_map = self.canonicalize_clinical_map(clinical_map)
        candidates = {}
        self.last_term_candidates = {}

        for category, term in self._term_category_pairs(clinical_map):
            term_norm = self.normalize(term)
            term_words = set(term_norm.split())
            if not term_words:
                continue

            scored_candidates = []
            for record in self.index_records:
                best_variant_score = 0.0
                matched_variant = None

                for variant_norm, variant_words in zip(record["variants"], record["variant_word_sets"]):
                    score = self._base_match_score(term_norm, term_words, variant_norm, variant_words)
                    if score > best_variant_score:
                        best_variant_score = score
                        matched_variant = variant_norm

                if best_variant_score < 35:
                    continue

                for code in record["codes"]:
                    scored_candidates.append(
                        {
                            "code": code,
                            "score": self._score_code_for_context(
                                term,
                                category,
                                code,
                                best_variant_score,
                                matched_variant or record["primary_term"],
                            ),
                            "matched_index_term": matched_variant or record["primary_term"],
                            "description": self.get_code_description(code),
                        }
                    )

            ranked_candidates = self._collapse_candidates(scored_candidates)[:5]
            if ranked_candidates:
                candidates[term] = ranked_candidates
                self.last_term_candidates[term] = {
                    "category": category,
                    "candidates": ranked_candidates,
                }

        return candidates

    def enforce_guidelines(self, clinical_map, candidates, setting="outpatient"):
        clinical_map = self.canonicalize_clinical_map(clinical_map)
        results = {
            "Diagnoses": set(),
            "Suspected Conditions": set(),
            "Symptoms": set(),
            "Signs": set(),
            "History": set(),
            "Procedures/Imaging": set(),
        }
        applied_refs = [
            "ICD-10-CM Official Guidelines: use Alphabetic Index then verify in Tabular List",
            "ICD-10-CM Official Guidelines: code to the highest specificity supported",
        ]

        for term, ranked_candidates in candidates.items():
            if not ranked_candidates:
                continue

            category = self.last_term_candidates.get(term, {}).get("category")
            top_candidate = ranked_candidates[0]
            code = top_candidate["code"]

            if category == "suspected_conditions":
                if setting == "outpatient":
                    applied_refs.append("Outpatient uncertain diagnoses are not coded as confirmed conditions")
                    continue
                applied_refs.append("Inpatient uncertain diagnoses may be coded as established at discharge")
                results["Diagnoses"].add(code)
                continue

            if category == "encounter_reason":
                if code.startswith("R"):
                    results["Symptoms"].add(code)
                else:
                    results["Diagnoses"].add(code)
            elif category in {"confirmed_diagnoses", "coexisting_conditions"}:
                results["Diagnoses"].add(code)
            elif category == "symptoms":
                if code.startswith("R"):
                    results["Symptoms"].add(code)
                else:
                    results["Signs"].add(code)
            elif category == "history_conditions":
                results["History"].add(code)
            elif category == "procedures":
                results["Procedures/Imaging"].add(code)

        final_results = {}
        for category, code_set in results.items():
            if not code_set:
                continue
            final_results[category] = self._drop_less_specific_family_codes(list(code_set))

        return final_results, applied_refs

    def _primary_priority_score(self, term, code, result_category):
        score = 0.0
        metadata = self.code_metadata.get(code, {})
        title_norm = metadata.get("title_norm", "")
        term_norm = self.normalize(term)

        if result_category == "Diagnoses":
            score += 60
        elif result_category in {"Symptoms", "Signs"}:
            score += 30

        high_priority_keywords = (
            "acute",
            "malignant",
            "fracture",
            "hemorrhage",
            "sepsis",
            "rupture",
            "perforation",
            "peritonitis",
            "abscess",
            "gangrene",
            "failure",
        )
        for keyword in high_priority_keywords:
            if keyword in term_norm:
                score += 8
            if keyword in title_norm:
                score += 6

        if "unspecified" in title_norm or "nos" in title_norm:
            score -= 8

        return score

    def select_primary_diagnosis(self, final_results, clinical_map):
        clinical_map = self.canonicalize_clinical_map(clinical_map)

        scored_options = []
        priority_buckets = (
            ("Diagnoses", clinical_map.get("encounter_reason", []), 24),
            ("Diagnoses", clinical_map.get("confirmed_diagnoses", []), 16),
            ("Diagnoses", clinical_map.get("coexisting_conditions", []), 8),
            ("Diagnoses", clinical_map.get("suspected_conditions", []), 12),
            ("Symptoms", clinical_map.get("encounter_reason", []), 18),
            ("Symptoms", clinical_map.get("symptoms", []), 8),
            ("Signs", clinical_map.get("symptoms", []), 6),
        )

        for result_category, source_terms, source_bonus in priority_buckets:
            allowed_codes = set(final_results.get(result_category, []))
            if not allowed_codes:
                continue

            for term in source_terms:
                candidate_info = self.last_term_candidates.get(term, {})
                if not candidate_info:
                    continue

                for candidate in candidate_info.get("candidates", []):
                    code = candidate["code"]
                    if code not in allowed_codes:
                        continue
                    total_score = (
                        candidate["score"]
                        + self._primary_priority_score(term, code, result_category)
                        + source_bonus
                    )
                    scored_options.append(
                        {
                            "code": code,
                            "description": self.get_code_description(code),
                            "category": result_category,
                            "term": term,
                            "score": total_score,
                        }
                    )
                    break

            if scored_options:
                break

        if not scored_options:
            return None

        return max(scored_options, key=lambda item: item["score"])

    def get_review_flags(self, final_results, clinical_map):
        clinical_map = self.canonicalize_clinical_map(clinical_map)
        flags = []
        all_selected_codes = {
            code for codes in final_results.values() if isinstance(codes, list) for code in codes
        }

        if not all_selected_codes:
            return ["No ICD-10-CM code could be confidently verified from the current documentation."]

        if not final_results.get("Diagnoses") and (final_results.get("Symptoms") or final_results.get("Signs")):
            flags.append("No confirmed diagnosis was verified, so the encounter is currently coded from symptoms/signs.")

        for term, info in self.last_term_candidates.items():
            candidates = info.get("candidates", [])
            if len(candidates) < 2:
                continue

            top_candidate = candidates[0]
            runner_up = candidates[1]
            if (
                top_candidate["code"] in all_selected_codes
                and top_candidate["score"] - runner_up["score"] < 8
            ):
                flags.append(
                    f"Close candidate match for '{term}': {top_candidate['code']} vs {runner_up['code']}."
                )

        encounter_reason_terms = clinical_map.get("encounter_reason", [])
        primary = self.select_primary_diagnosis(final_results, clinical_map)
        if encounter_reason_terms and primary and primary["term"] not in encounter_reason_terms:
            flags.append(
                f"Primary diagnosis was selected from '{primary['term']}' instead of the extracted encounter reason."
            )

        return flags[:3]

    def sanitize_results(self, results, setting="outpatient"):
        if not isinstance(results, dict):
            return {}

        cleaned_results = {}
        allowed_categories = {
            "Diagnoses",
            "Suspected Conditions",
            "Symptoms",
            "Signs",
            "History",
            "Procedures/Imaging",
        }

        for category, codes in results.items():
            if category not in allowed_categories:
                continue
            target_category = category
            if category == "Suspected Conditions":
                if setting == "outpatient":
                    continue
                target_category = "Diagnoses"

            if not isinstance(codes, list):
                codes = [codes]

            normalized_codes = []
            for code in codes:
                clean_code = self.clean_code(code)
                if self.is_valid_code(clean_code):
                    normalized_codes.append(clean_code)

            normalized_codes = self._drop_less_specific_family_codes(normalized_codes)
            if normalized_codes:
                cleaned_results.setdefault(target_category, [])
                cleaned_results[target_category].extend(normalized_codes)

        for category, codes in list(cleaned_results.items()):
            cleaned_results[category] = self._drop_less_specific_family_codes(codes)

        return cleaned_results

    def finalize_results(self, refined_results, initial_results, setting="outpatient"):
        cleaned_refined = self.sanitize_results(refined_results, setting=setting)
        if cleaned_refined:
            return cleaned_refined
        return self.sanitize_results(initial_results, setting=setting)
