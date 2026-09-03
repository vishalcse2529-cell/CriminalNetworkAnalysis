"""
Entity Extractor Module for Criminal Network Analysis System (SIH26189)
Extracts Person Names, Phone Numbers, and Locations from FIR descriptions
using regex, curated gazetteers, and optional spaCy NER with zero-crash fallbacks.
"""

from __future__ import annotations
import re
from typing import List, Dict, Set, Optional, Any
import pandas as pd

# Try loading spaCy if available
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None

# Curated gazetteer of Indian locations/towns/neighborhoods frequently in crime reports
KNOWN_LOCATIONS = {
    "Gandhipuram", "RS Puram", "Peelamedu", "Town Hall", "Coimbatore", "Erode", "Salem",
    "Madurai", "Chennai", "Bangalore", "Tirupur", "Trichy", "Hosur", "Dindigul", "Avinashi",
    "Saravanampatti", "Singanallur", "Ukkadam", "Saibaba Colony", "Vellore", "Kochi", "Hyderabad"
}

# Curated gazetteer of known suspects / persons in synthetic datasets
KNOWN_PERSONS = {
    "Ravi Kumar", "Arun Raj", "Suresh", "Vikram Singh", "Priya Sharma", "Rajesh Nair",
    "Amit Patel", "Anand Verma", "Dinesh Karthik", "Manoj Tiwari", "Vijay Sethi",
    "Karthik Subbaraj", "Meena Sundaram", "Deepa Loganathan"
}

PHONE_REGEX = re.compile(r'(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}|\b[6-9]\d{9}\b')


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extracts 10-digit Indian mobile numbers from unstructured text using regex.
    """
    if not text or not isinstance(text, str):
        return []
    
    matches = PHONE_REGEX.findall(text)
    cleaned = []
    for m in matches:
        digits = "".join(c for c in m if c.isdigit())
        if len(digits) > 10 and digits.startswith("91"):
            digits = digits[2:]
        if len(digits) == 10 and digits not in cleaned:
            cleaned.append(digits)
    return cleaned


def extract_locations(text: str, custom_locations: Optional[Set[str]] = None) -> List[str]:
    """
    Extracts location names from text using gazetteer lookup and optional spaCy NER.
    """
    if not text or not isinstance(text, str):
        return []

    found: Set[str] = set()
    loc_pool = KNOWN_LOCATIONS.union(custom_locations or set())

    # 1. Gazetteer matching (case-insensitive boundary match)
    for loc in loc_pool:
        pattern = rf'\b{re.escape(loc)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            found.add(loc)

    # 2. spaCy NER (if loaded)
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC", "FAC"):
                    val = ent.text.strip()
                    if len(val) > 2 and not any(ch.isdigit() for ch in val):
                        found.add(val)
        except Exception:
            pass

    return sorted(list(found))


def extract_persons(text: str, custom_persons: Optional[Set[str]] = None) -> List[str]:
    """
    Extracts person names using gazetteer matching, capitalized name patterns,
    and optional spaCy NER.
    """
    if not text or not isinstance(text, str):
        return []

    found: Set[str] = set()
    person_pool = KNOWN_PERSONS.union(custom_persons or set())

    # 1. Gazetteer match
    for person in person_pool:
        pattern = rf'\b{re.escape(person)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            found.add(person)

    # 2. spaCy NER (if loaded)
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    val = ent.text.strip()
                    # Filter out non-person words
                    if len(val) > 3 and val not in KNOWN_LOCATIONS and not any(ch.isdigit() for ch in val):
                        found.add(val)
        except Exception:
            pass

    # 3. Capitalized 2-word heuristic (e.g. "Ravi Kumar", "Vikram Singh")
    name_candidates = re.findall(r'\b[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}\b', text)
    stopwords = {"Bus Stand", "Town Hall", "Avinashi Road", "Cash Transit", "CCTV Cameras", "Chassis Numbers"}
    for candidate in name_candidates:
        if candidate not in stopwords and candidate not in KNOWN_LOCATIONS:
            if any(cand_part in p for p in person_pool for cand_part in candidate.split()):
                found.add(candidate)

    return sorted(list(found))


def extract_all_entities(text: str, custom_persons: Optional[Set[str]] = None, custom_locations: Optional[Set[str]] = None) -> Dict[str, List[str]]:
    """
    Extracts all entities (Persons, Phone Numbers, Locations) from narrative text.
    """
    return {
        "persons": extract_persons(text, custom_persons),
        "phone_numbers": extract_phone_numbers(text),
        "locations": extract_locations(text, custom_locations),
    }


def extract_entities_from_fir_row(row: pd.Series) -> Dict[str, List[str]]:
    """
    Combines structured FIR columns (persons, phone_numbers, location)
    with entities extracted from the narrative description field.
    """
    desc = str(row.get("description", ""))
    extracted = extract_all_entities(desc)

    # Incorporate structured 'persons' column (separated by ';' or ',')
    struct_persons_raw = str(row.get("persons", ""))
    if struct_persons_raw and struct_persons_raw.lower() != "nan":
        for p in re.split(r'[;,]\s*', struct_persons_raw):
            p_clean = p.strip()
            if p_clean and p_clean not in extracted["persons"]:
                extracted["persons"].append(p_clean)

    # Incorporate structured 'phone_numbers' column
    struct_phones_raw = str(row.get("phone_numbers", ""))
    if struct_phones_raw and struct_phones_raw.lower() != "nan":
        for ph in re.split(r'[;,]\s*', struct_phones_raw):
            digits = "".join(c for c in ph if c.isdigit())
            if len(digits) >= 10:
                ph_10 = digits[-10:]
                if ph_10 not in extracted["phone_numbers"]:
                    extracted["phone_numbers"].append(ph_10)

    # Incorporate structured 'location' column
    struct_loc = str(row.get("location", "")).strip()
    if struct_loc and struct_loc.lower() != "nan" and struct_loc not in extracted["locations"]:
        extracted["locations"].append(struct_loc)

    return extracted
