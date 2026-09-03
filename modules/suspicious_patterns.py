"""
Suspicious Pattern Detection Module for Criminal Network Analysis System (SIH26189)
Rule-based detection engines identifying investigative leads:
- Pattern 1: High Communication Burst
- Pattern 2: Pre-Crime Communication
- Pattern 3: Unusual Financial Flows & Mule Layering
- Pattern 4: Cross-Crime Syndication
- Pattern 5: Shared Burner Device
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import timedelta
import re
from .entity_extractor import extract_entities_from_fir_row


def detect_high_communication(cdr_df: pd.DataFrame, time_window_hours: int = 3, min_unique_contacts: int = 5) -> List[Dict[str, Any]]:
    """
    Pattern 1: Detects single phone numbers contacting multiple distinct numbers
    within a short rolling time window (burst communication).
    """
    patterns = []
    if cdr_df is None or cdr_df.empty:
        return patterns

    df = cdr_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    callers = df["caller_number"].unique()

    for caller in callers:
        c_calls = df[df["caller_number"] == caller].sort_values("timestamp")
        if len(c_calls) < min_unique_contacts:
            continue

        for i, start_row in c_calls.iterrows():
            start_time = start_row["timestamp"]
            end_time = start_time + timedelta(hours=time_window_hours)
            window_calls = c_calls[(c_calls["timestamp"] >= start_time) & (c_calls["timestamp"] <= end_time)]
            unique_contacts = window_calls["receiver_number"].unique()

            if len(unique_contacts) >= min_unique_contacts:
                patterns.append({
                    "id": f"PAT-COMM-{caller}-{start_time.strftime('%Y%m%d%H%M')}",
                    "pattern_type": "High Communication Burst",
                    "severity": "HIGH",
                    "severity_label": "🔴 HIGH PRIORITY",
                    "title": f"Rapid Outbound Communication Burst ({caller})",
                    "summary": f"{caller} contacted {len(unique_contacts)} distinct numbers within a {time_window_hours}-hour period.",
                    "details": {
                        "Target Phone": caller,
                        "Distinct Contacts Count": len(unique_contacts),
                        "Contacts Reached": list(unique_contacts)[:8],
                        "Time Window": f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%H:%M')}",
                        "Tower Locations": list(window_calls["tower_location"].unique())
                    },
                    "entities_involved": [caller] + list(unique_contacts),
                    "lead_note": "Indicates tactical coordination, blast phishing dispatch, or panic syndication calls."
                })
                # Prevent duplicate alerts for the same caller burst
                break

    return patterns


def detect_pre_crime_communication(
    fir_df: pd.DataFrame,
    cdr_df: pd.DataFrame,
    pre_window_hours: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Pattern 2: Checks whether telephone communications between suspects
    occurred shortly before an FIR incident time.
    """
    patterns = []
    if fir_df is None or fir_df.empty or cdr_df is None or cdr_df.empty:
        return patterns

    firs = fir_df.copy()
    firs["date"] = pd.to_datetime(firs["date"], errors="coerce")
    firs = firs.dropna(subset=["date"])

    cdrs = cdr_df.copy()
    cdrs["timestamp"] = pd.to_datetime(cdrs["timestamp"], errors="coerce")
    cdrs = cdrs.dropna(subset=["timestamp"])

    for _, fir in firs.iterrows():
        fir_id = str(fir["fir_id"])
        crime_time = fir["date"]
        crime_type = str(fir.get("crime_type", "Crime"))
        window_start = crime_time - timedelta(hours=pre_window_hours)

        # Get suspects & phones associated with this FIR
        entities = extract_entities_from_fir_row(fir)
        fir_phones = set(entities["phone_numbers"])
        fir_persons = entities["persons"]

        if not fir_phones:
            continue

        # Look for calls between co-accused suspect phones in the pre-crime window
        window_calls = cdrs[
            (cdrs["timestamp"] >= window_start) &
            (cdrs["timestamp"] <= crime_time) &
            (cdrs["caller_number"].isin(fir_phones)) &
            (cdrs["receiver_number"].isin(fir_phones))
        ]

        if len(window_calls) >= 2:
            involved_callers = set(window_calls["caller_number"]).union(set(window_calls["receiver_number"]))
            patterns.append({
                "id": f"PAT-PRECRIME-{fir_id}",
                "pattern_type": "Pre-Crime Communication",
                "severity": "HIGH",
                "severity_label": "🔴 HIGH PRIORITY",
                "title": f"Pre-Crime Communication Before {fir_id} ({crime_type})",
                "summary": f"{len(window_calls)} calls detected between co-suspects within {pre_window_hours} hours prior to {fir_id}.",
                "details": {
                    "Related FIR": fir_id,
                    "Crime Type": crime_type,
                    "Incident Time": crime_time.strftime("%Y-%m-%d %H:%M"),
                    "Pre-Crime Calls Detected": len(window_calls),
                    "Active Phone Numbers": list(involved_callers),
                    "Named Suspects in FIR": fir_persons,
                    "Tower Locations": list(window_calls["tower_location"].unique())
                },
                "entities_involved": fir_persons + list(involved_callers),
                "lead_note": f"Strong temporal coordination between co-accused immediately preceding {crime_type} incident."
            })

    return patterns


def detect_unusual_financial_flow(txn_df: pd.DataFrame, high_threshold: float = 100000.0) -> List[Dict[str, Any]]:
    """
    Pattern 3: Detects unusual financial flows including:
    - Rapid successive transfers between the same entities (< 24 hours)
    - Multi-hop layering / mule chains (A -> B -> C within 24h)
    - Unusually large transfers exceeding threshold
    """
    patterns = []
    if txn_df is None or txn_df.empty:
        return patterns

    txns = txn_df.copy()
    txns["timestamp"] = pd.to_datetime(txns["timestamp"], errors="coerce")
    txns = txns.dropna(subset=["timestamp"]).sort_values("timestamp")

    seen_chains = set()

    # 1. Multi-hop layering / mule chain: A -> B followed by B -> C within 24 hours
    for i, t1 in txns.iterrows():
        a = t1["sender_id"]
        b = t1["receiver_id"]
        t1_time = t1["timestamp"]
        amt1 = float(t1["amount"])

        # Look for subsequent transfer where B sends money to someone else within 24 hours
        downstream = txns[
            (txns["sender_id"] == b) &
            (txns["receiver_id"] != a) &
            (txns["timestamp"] >= t1_time) &
            (txns["timestamp"] <= t1_time + timedelta(hours=24))
        ]

        for j, t2 in downstream.iterrows():
            c = t2["receiver_id"]
            amt2 = float(t2["amount"])
            chain_key = (a, b, c, t1_time.strftime("%Y-%m-%d"))
            if chain_key in seen_chains:
                continue
            seen_chains.add(chain_key)

            patterns.append({
                "id": f"PAT-FIN-CHAIN-{t1['transaction_id']}-{t2['transaction_id']}",
                "pattern_type": "Layered Financial Flow (Mule Chain)",
                "severity": "HIGH",
                "severity_label": "🔴 HIGH PRIORITY",
                "title": f"Layered Transfer Chain: {a} -> {b} -> {c}",
                "summary": f"{a} transferred ₹{amt1:,.0f} to {b}, followed by {b} transferring ₹{amt2:,.0f} to {c} within 24 hours.",
                "details": {
                    "Originator": a,
                    "Intermediary (Mule)": b,
                    "Destination": c,
                    "Initial Transfer": f"₹{amt1:,.0f} on {t1_time.strftime('%Y-%m-%d %H:%M')}",
                    "Follow-up Transfer": f"₹{amt2:,.0f} on {t2['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                    "Locations": [str(t1.get("location", "")), str(t2.get("location", ""))]
                },
                "entities_involved": [a, b, c],
                "lead_note": "Characteristic smurfing/layering pattern designed to distance illicit proceeds from origin."
            })

    # 2. Repeated transfers between same sender and receiver within 24 hours
    pairs = txns.groupby(["sender_id", "receiver_id"])
    for (s, r), group in pairs:
        if len(group) >= 2:
            group_sorted = group.sort_values("timestamp")
            for k in range(len(group_sorted) - 1):
                cur = group_sorted.iloc[k]
                nxt = group_sorted.iloc[k + 1]
                time_diff = nxt["timestamp"] - cur["timestamp"]
                if time_diff <= timedelta(hours=24):
                    patterns.append({
                        "id": f"PAT-FIN-REPEAT-{cur['transaction_id']}-{nxt['transaction_id']}",
                        "pattern_type": "Repeated Structured Transfers",
                        "severity": "MEDIUM",
                        "severity_label": "🟠 MEDIUM PRIORITY",
                        "title": f"Repeated Rapid Transfers: {s} -> {r}",
                        "summary": f"{s} transferred ₹{float(cur['amount']):,.0f} and ₹{float(nxt['amount']):,.0f} to {r} within {time_diff.total_seconds() / 3600:.1f} hours.",
                        "details": {
                            "Sender": s,
                            "Receiver": r,
                            "Transfer 1": f"₹{float(cur['amount']):,.0f} at {cur['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                            "Transfer 2": f"₹{float(nxt['amount']):,.0f} at {nxt['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                            "Total Transferred": f"₹{float(cur['amount']) + float(nxt['amount']):,.0f}"
                        },
                        "entities_involved": [s, r],
                        "lead_note": "Repeated transfers in short windows may indicate structuring to stay beneath banking monitoring limits."
                    })
                    break

    # 3. High Value Transaction
    large_txns = txns[txns["amount"] >= high_threshold]
    for _, lt in large_txns.iterrows():
        s = lt["sender_id"]
        r = lt["receiver_id"]
        amt = float(lt["amount"])
        patterns.append({
            "id": f"PAT-FIN-LARGE-{lt['transaction_id']}",
            "pattern_type": "High Value Transaction",
            "severity": "MEDIUM",
            "severity_label": "🟠 MEDIUM PRIORITY",
            "title": f"High Value Transaction: ₹{amt:,.0f} ({s} -> {r})",
            "summary": f"Unusually large transfer of ₹{amt:,.0f} executed from {s} to {r} via {lt.get('location', 'Unknown')}.",
            "details": {
                "Transaction ID": lt["transaction_id"],
                "Sender": s,
                "Receiver": r,
                "Amount": f"₹{amt:,.0f}",
                "Timestamp": lt["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "Location": lt.get("location", "Unknown")
            },
            "entities_involved": [s, r],
            "lead_note": "Significant liquidity transfer; examine account origin and underlying commercial justification."
        })

    return patterns


def detect_cross_crime_associations(fir_df: pd.DataFrame, min_crime_types: int = 2) -> List[Dict[str, Any]]:
    """
    Pattern 4: Identifies individuals who appear across FIRs representing
    multiple distinct categories of crime (e.g. Robbery + Cybercrime + Fraud).
    """
    patterns = []
    if fir_df is None or fir_df.empty:
        return patterns

    person_crimes: Dict[str, Dict[str, List[str]]] = {}

    for _, row in fir_df.iterrows():
        fir_id = str(row.get("fir_id", "")).strip()
        crime_type = str(row.get("crime_type", "Unknown")).strip()
        entities = extract_entities_from_fir_row(row)

        for person in entities["persons"]:
            if person not in person_crimes:
                person_crimes[person] = {}
            person_crimes[person].setdefault(crime_type, []).append(fir_id)

    for person, crimes in person_crimes.items():
        if len(crimes) >= min_crime_types:
            all_firs = [fid for f_list in crimes.values() for fid in f_list]
            patterns.append({
                "id": f"PAT-CROSSCRIME-{person.replace(' ', '_')}",
                "pattern_type": "Cross-Crime Association",
                "severity": "MEDIUM",
                "severity_label": "🟠 MEDIUM PRIORITY",
                "title": f"Multi-Offense Syndicate Linkage: {person}",
                "summary": f"{person} appears in records associated with {len(crimes)} different crime types: {', '.join(crimes.keys())}.",
                "details": {
                    "Individual": person,
                    "Distinct Crime Categories": list(crimes.keys()),
                    "FIR Breakdown": {c: fids for c, fids in crimes.items()},
                    "Total Linked FIRs": len(all_firs)
                },
                "entities_involved": [person],
                "lead_note": "Indicates organized criminal syndicate capability operating across multiple illicit domains."
            })

    return patterns


def detect_shared_burner_devices(fir_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Pattern 5: Identifies phone numbers shared across multiple distinct suspects
    in different FIR reports.
    """
    patterns = []
    if fir_df is None or fir_df.empty:
        return patterns

    phone_to_persons: Dict[str, Dict[str, List[str]]] = {}

    for _, row in fir_df.iterrows():
        fir_id = str(row.get("fir_id", "")).strip()
        entities = extract_entities_from_fir_row(row)
        persons = entities["persons"]
        phones = entities["phone_numbers"]

        if len(persons) == len(phones):
            for p, ph in zip(persons, phones):
                phone_to_persons.setdefault(ph, {}).setdefault(p, []).append(fir_id)
        else:
            for ph in phones:
                for p in persons:
                    phone_to_persons.setdefault(ph, {}).setdefault(p, []).append(fir_id)

    for phone, p_dict in phone_to_persons.items():
        if len(p_dict) >= 2:
            patterns.append({
                "id": f"PAT-BURNER-{phone}",
                "pattern_type": "Shared Communication Hub / Burner Device",
                "severity": "HIGH",
                "severity_label": "🔴 HIGH PRIORITY",
                "title": f"Shared Device / Number: {phone}",
                "summary": f"Phone {phone} is directly linked to {len(p_dict)} distinct individuals across case records.",
                "details": {
                    "Phone Number": phone,
                    "Associated Persons": list(p_dict.keys()),
                    "Cases Implicated": [fid for flist in p_dict.values() for fid in flist]
                },
                "entities_involved": [phone] + list(p_dict.keys()),
                "lead_note": "Indicates shared operational hardware, syndicate burner phone, or coordinated communications proxy."
            })

    return patterns


def detect_all_suspicious_patterns(
    fir_df: Optional[pd.DataFrame] = None,
    cdr_df: Optional[pd.DataFrame] = None,
    txn_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Consolidates rule-based pattern detectors across all datasets.
    Returns prioritized list of investigative leads.
    """
    all_patterns = []

    if cdr_df is not None and not cdr_df.empty:
        all_patterns.extend(detect_high_communication(cdr_df))

    if fir_df is not None and not fir_df.empty and cdr_df is not None and not cdr_df.empty:
        all_patterns.extend(detect_pre_crime_communication(fir_df, cdr_df))

    if txn_df is not None and not txn_df.empty:
        all_patterns.extend(detect_unusual_financial_flow(txn_df))

    if fir_df is not None and not fir_df.empty:
        all_patterns.extend(detect_cross_crime_associations(fir_df))
        all_patterns.extend(detect_shared_burner_devices(fir_df))

    # Priority sort: HIGH first, then MEDIUM, then LOW
    priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_patterns.sort(key=lambda p: priority_order.get(p.get("severity", "LOW"), 4))

    return all_patterns
