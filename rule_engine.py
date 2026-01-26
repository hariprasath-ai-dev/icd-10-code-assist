import json
import re

class RuleEngine:
    def __init__(self):
        self.codes = json.load(open('codes.json'))['codes']
        self.index = json.load(open('index.json'))['terms']
        self.tabular = json.load(open('tabular.json'))['codes']
        self.rules = json.load(open('rules.json'))['rules']

    def normalize(self, text):
        # Deterministic normalization for primary lookup keys
        text = text.lower()
        text = text.replace("'", "")
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return " ".join(text.split()).strip()

    def discover_candidates(self, clinical_map):
        candidates = {}
        all_terms = (clinical_map['confirmed_diagnoses'] + 
                     clinical_map['suspected_conditions'] + 
                     clinical_map['symptoms'] +
                     clinical_map['history_conditions'] +
                     clinical_map.get('procedures', []))
        
        index_keys = list(self.index.keys())
        index_word_sets = {pk: set(pk.split()) for pk in index_keys}

        for term in all_terms:
            norm = self.normalize(term)
            valid_codes = []
            
            if norm in self.index and self.index[norm].get("codes"):
                raw_codes = self.index[norm]["codes"]
                valid_codes = [c.replace(".", "") for c in raw_codes if c.replace(".", "") in self.codes]
            
            if not valid_codes:
                # Improved Fuzzy/Keyword discovery
                term_words = set(norm.split())
                if not term_words: continue
                
                scored_matches = []
                for pk, word_set in index_word_sets.items():
                    intersection = term_words.intersection(word_set)
                    overlap_size = len(intersection)
                    if overlap_size == 0: continue
                    
                    is_significant = (overlap_size >= 2) or (overlap_size == len(term_words))
                    if not is_significant: continue
                    
                    score = (overlap_size / len(term_words)) * (overlap_size / len(word_set))
                    has_codes = bool("codes" in self.index[pk] and self.index[pk]["codes"])
                    if has_codes: score *= 2.0
                    scored_matches.append((pk, score, has_codes))
                
                if scored_matches:
                    scored_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
                    top_pk = scored_matches[0][0]
                    if scored_matches[0][1] >= 0.2:
                        raw_codes = self.index[top_pk].get("codes", [])
                        valid_codes = [c.replace(".", "") for c in raw_codes if c.replace(".", "") in self.codes]
            
            if valid_codes:
                candidates[term] = valid_codes
                    
        return candidates

    def enforce_guidelines(self, clinical_map, candidates, setting='outpatient'):
        results = {
            "Diagnoses": set(),
            "Suspected Conditions": set(),
            "Symptoms": set(),
            "Signs": set(),
            "History": set(),
            "Procedures/Imaging": set()
        }
        applied_refs = ["ICD-10-CM General Guidelines v2026"]

        for term, codes in candidates.items():
            if not codes: continue
            code = codes[0] # Use primary candidate

            if term in clinical_map['confirmed_diagnoses']:
                results["Diagnoses"].add(code)
            elif term in clinical_map['suspected_conditions']:
                results["Suspected Conditions"].add(code)
            elif term in clinical_map['symptoms']:
                if code.startswith("R"): results["Symptoms"].add(code)
                else: results["Signs"].add(code)
            elif term in clinical_map['history_conditions']:
                results["History"].add(code)
            elif term in clinical_map.get('procedures', []):
                results["Procedures/Imaging"].add(code)

        final_results = {k: sorted(list(v)) for k, v in results.items() if v}
        return final_results, applied_refs
