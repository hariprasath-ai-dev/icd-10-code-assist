import json
import xml.etree.ElementTree as ET
import os
import re

def clean_code(code):
    if not code: return None
    return code.replace(".", "").strip()

def process_codes():
    print("Processing codes.json...")
    codes = {}
    file_path = r'c:\Users\harit\Documents\codedo\icd10cm\icd10cm_codes_2026.txt'
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            code = line[:7].strip()
            desc = line[7:].strip()
            codes[code] = {"description": desc}
    
    output = {
        "metadata": { "version": "2026", "type": "ICD-10-CM" },
        "codes": codes
    }
    with open('codes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print("codes.json created.")

def process_index():
    print("Processing index.json...")
    file_path = r'c:\Users\harit\Documents\codedo\icd10cm\icd10cm_index_2026.xml'
    tree = ET.parse(file_path)
    root = tree.getroot()
    terms = {}
    
    def normalize_key(text):
        text = text.lower()
        text = text.replace("'", "")
        # Remove commas and parentheses to keep it clean
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return " ".join(text.split()).strip()

    def get_title_variants(title_el):
        # primary: text outside nemod
        # full: all text
        primary_parts = []
        full_parts = []
        
        # Iterating using iter() gives all sub-elements.
        # title_el.text is text before first child
        if title_el.text:
            primary_parts.append(title_el.text)
            full_parts.append(title_el.text)
            
        for child in title_el:
            if child.tag == 'nemod':
                if child.text: full_parts.append(child.text)
                if child.tail:
                    primary_parts.append(child.tail)
                    full_parts.append(child.tail)
            else:
                # Other tags (rare in index titles)
                child_text = "".join(child.itertext())
                primary_parts.append(child_text)
                full_parts.append(child_text)
                if child.tail:
                    primary_parts.append(child.tail)
                    full_parts.append(child.tail)
                    
        return "".join(primary_parts).strip(), "".join(full_parts).strip()

    def process_element(element, current_path_parts=[]):
        title_el = element.find('title')
        if title_el is None: return
        
        primary_title, full_title = get_title_variants(title_el)
        
        # Use primary for hierarchy path to avoid bloating keys with (modifiers)
        new_path_parts = current_path_parts + [primary_title]
        raw_primary_phrase = " ".join(new_path_parts).strip()
        
        pk = normalize_key(raw_primary_phrase)
        if not pk: return

        entry_template = {}
        code_el = element.find('code')
        if code_el is not None:
            entry_template["codes"] = [clean_code(code_el.text)]
            
        see_el = element.find('see')
        if see_el is not None: entry_template["see"] = see_el.text.lower()
        see_also_el = element.find('seeAlso')
        if see_also_el is not None: entry_template["seeAlso"] = see_also_el.text.lower()

        if entry_template or element.findall('term'):
            if pk not in terms:
                terms[pk] = { "codes": [], "aliases": [] }
                if "see" in entry_template: terms[pk]["see"] = entry_template["see"]
                if "seeAlso" in entry_template: terms[pk]["seeAlso"] = entry_template["seeAlso"]
            
            # Add full phrase (with modifiers) as alias
            full_phrase = " ".join(current_path_parts + [full_title]).strip()
            norm_full = normalize_key(full_phrase)
            if norm_full != pk and norm_full not in terms[pk]["aliases"]:
                terms[pk]["aliases"].append(norm_full)
            
            # Add verbatim lower as alias if different
            verbatim = raw_primary_phrase.lower()
            if verbatim != pk and verbatim not in terms[pk]["aliases"]:
                terms[pk]["aliases"].append(verbatim)

            if "codes" in entry_template:
                for c in entry_template["codes"]:
                    if c not in terms[pk]["codes"]:
                        terms[pk]["codes"].append(c)

        for subterm in element.findall('term'):
            process_element(subterm, new_path_parts)

    for letter in root.findall('letter'):
        for main_term in letter.findall('mainTerm'):
            process_element(main_term)
            
    # Cleanup
    for pk in list(terms.keys()):
        if not terms[pk]["codes"]: del terms[pk]["codes"]
        if "aliases" in terms[pk] and not terms[pk]["aliases"]: del terms[pk]["aliases"]

    output = {
        "metadata": { "version": "2026", "source": "Alphabetic Index" },
        "terms": terms
    }
    with open('index.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print("index.json created.")

def process_tabular():
    print("Processing tabular.json...")
    file_path = r'c:\Users\harit\Documents\codedo\icd10cm\icd10cm_tabular_2026.xml'
    tree = ET.parse(file_path)
    root = tree.getroot()
    codes = {}
    
    def parse_instruction(element, tag):
        results = []
        found = element.find(tag)
        if found is not None:
            for note in found.findall('note'):
                if note.text: results.append(note.text.strip())
        return results

    def process_diag(diag, parent_name=None):
        name_el = diag.find('name')
        desc_el = diag.find('desc')
        if name_el is None or desc_el is None: return
        
        name = clean_code(name_el.text)
        
        includes = []
        for inc in diag.findall('inclusionTerm'):
            for note in inc.findall('note'):
                if note.text: includes.append(note.text.strip())
        includes.extend(parse_instruction(diag, 'includes'))
        
        excludes1 = [clean_code(c) for c in parse_instruction(diag, 'excludes1')]
        excludes2 = [clean_code(c) for c in parse_instruction(diag, 'excludes2')]
        notes = parse_instruction(diag, 'note')
        use_additional_code = parse_instruction(diag, 'useAdditionalCode')
        code_first = parse_instruction(diag, 'codeFirst')
        code_also = parse_instruction(diag, 'codeAlso')
        
        code_data = {
          "title": desc_el.text,
          "parent": clean_code(parent_name),
          "includes": includes,
          "excludes1": excludes1,
          "excludes2": excludes2,
          "notes": notes,
          "use_additional_code": use_additional_code,
          "code_first": code_first
        }
        if code_also: code_data["code_also"] = code_also

        codes[name] = code_data
        
        for subdiag in diag.findall('diag'):
            process_diag(subdiag, name)

    for chapter in root.findall('chapter'):
        for section in chapter.findall('section'):
            for diag in section.findall('diag'):
                process_diag(diag)
                
    output = {
        "metadata": { "version": "2026", "source": "Tabular List" },
        "codes": codes
    }
    with open('tabular.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print("tabular.json created.")

def create_rules():
    print("Creating rules.json...")
    rules = [
        {
          "rule_id": "SYMPTOMS_IN_ABSENCE_OF_DIAGNOSIS",
          "source_section": "Section I.B.4",
          "source_text": "Codes that describe symptoms and signs, as opposed to diagnoses, are acceptable for reporting purposes when a related definitive diagnosis has not been established (confirmed) by the provider.",
          "trigger_keywords": [],
          "interpretation": "Symptoms and signs may be coded only if the provider has not established a definitive, confirmed diagnosis.",
          "action": "assign_symptom_codes_only_when_diagnosis_is_unconfirmed"
        },
        {
          "rule_id": "INTEGRAL_SYMPTOMS_NOT_CODED",
          "source_section": "Section I.B.5",
          "source_text": "Signs and symptoms that are associated routinely with a disease process should not be assigned as additional codes, unless otherwise instructed by the classification.",
          "trigger_keywords": [],
          "interpretation": "When a routine symptom is part of a confirmed disease process, do not code the symptom separately unless instructed.",
          "action": "do_not_assign_integral_symptom_codes"
        },
        {
          "rule_id": "NON_INTEGRAL_SYMPTOMS_CODED",
          "source_section": "Section I.B.6",
          "source_text": "Additional signs and symptoms that may not be associated routinely with a disease process should be coded when present.",
          "trigger_keywords": [],
          "interpretation": "Signs or symptoms that are not typically part of a confirmed disease process must be coded as additional information.",
          "action": "assign_non_integral_symptom_codes"
        },
        {
          "rule_id": "ACUTE_AND_CHRONIC_CODING",
          "source_section": "Section I.B.8",
          "source_text": "If the same condition is described as both acute (subacute) and chronic, and separate subentries exist in the Alphabetic Index at the same indentation level, code both and sequence the acute (subacute) code first.",
          "trigger_keywords": ["acute", "subacute", "chronic"],
          "interpretation": "When a condition is both acute and chronic, assign codes for both if the index provides separate entries at the same level, with the acute code appearing first.",
          "action": "assign_both_codes_record_acute_code_first"
        },
        {
          "rule_id": "SEQUELA_CODING_ORDER",
          "source_section": "Section I.B.10",
          "source_text": "Coding of sequela generally requires two codes sequenced in the following order: the condition or nature of the sequela is sequenced first. The sequela code is sequenced second.",
          "trigger_keywords": ["sequela"],
          "interpretation": "When coding a late effect (sequela), the code for the resulting condition (residual) must be listed before the code identifying the original cause (sequela).",
          "action": "sequence_residual_condition_first_then_sequela_code"
        },
        {
          "rule_id": "IMPENDING_OR_THREATENED_NOT_OCCURRED",
          "source_section": "Section I.B.11",
          "source_text": "If it did not occur, reference the Alphabetic Index to determine if the condition has a subentry term for \"impending\" or \"threatened\"... If the subterms are not listed, code the existing underlying condition(s) and not the condition described as impending or threatened.",
          "trigger_keywords": ["impending", "threatened"],
          "interpretation": "For conditions described as impending or threatened that did not happen, use specific index entries for those terms; if none exist, code the underlying symptoms or conditions.",
          "action": "check_index_for_impending_subterms_else_code_symptoms"
        },
        {
          "rule_id": "UNCERTAIN_DIAGNOSIS_INPATIENT",
          "source_section": "Section II.H",
          "source_text": "If the diagnosis documented at the time of discharge is qualified as \"probable,\" \"suspected,\" \"likely,\" \"questionable,\" \"possible,\" or \"still to be ruled out,\" \"compatible with,\" \"consistent with,\" or other similar terms indicating uncertainty, code the condition as if it existed or was established.",
          "trigger_keywords": ["probable", "suspected", "likely", "questionable", "possible", "still to be ruled out", "compatible with", "consistent with"],
          "interpretation": "In inpatient hospital settings, conditions described with terms of uncertainty at discharge should be coded as if the diagnosis was confirmed.",
          "action": "assign_diagnosis_code_as_if_confirmed"
        },
        {
          "rule_id": "UNCERTAIN_DIAGNOSIS_OUTPATIENT",
          "source_section": "Section IV.H",
          "source_text": "Do not code diagnoses documented as \"probable\", \"suspected,\" \"questionable,\" \"rule out,\" \"compatible with,\" \"consistent with,\" or \"working diagnosis\" or other similar terms indicating uncertainty. Rather, code the condition(s) to the highest degree of certainty for that encounter/visit, such as symptoms, signs, abnormal test results, or other reason for the visit.",
          "trigger_keywords": ["probable", "suspected", "questionable", "rule out", "compatible with", "consistent with", "working diagnosis"],
          "interpretation": "In outpatient settings, do not code uncertain diagnoses; instead, code to the highest level of certainty, such as symptoms or abnormal test results.",
          "action": "assign_symptom_or_sign_codes_only"
        }
    ]
    output = { "metadata": { "version": "2026", "source": "Official ICD-10-CM Guidelines" }, "rules": rules }
    with open('rules.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print("rules.json created.")

if __name__ == "__main__":
    process_codes()
    process_index()
    process_tabular()
    create_rules()
