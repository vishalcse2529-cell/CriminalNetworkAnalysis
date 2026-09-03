"""
Data Loader Module for Criminal Network Analysis System (SIH26189)
Handles loading, validation, cleaning, and normalization of FIR, CDR, and Transaction datasets.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union
import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

REQUIRED_FIR_COLUMNS = ["fir_id", "date", "crime_type", "description", "location", "persons", "phone_numbers"]
REQUIRED_CDR_COLUMNS = ["caller_number", "receiver_number", "timestamp", "duration", "tower_location"]
REQUIRED_TXN_COLUMNS = ["transaction_id", "sender_id", "receiver_id", "amount", "timestamp", "location"]


def clean_phone_str(phone: Any) -> str:
    """Standardizes phone number strings, stripping whitespace and prefixes."""
    if pd.isna(phone):
        return ""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


def load_fir_data(source: Optional[Union[str, Path, Any]] = None) -> pd.DataFrame:
    """
    Loads FIR dataset from a path, uploaded file buffer, or default dataset.
    Normalizes missing fields and datetime columns.
    """
    if source is None:
        source = DEFAULT_DATA_DIR / "fir_data.csv"

    try:
        df = pd.read_csv(source)
    except Exception as e:
        # Fallback to default if custom file fails
        if source != DEFAULT_DATA_DIR / "fir_data.csv" and (DEFAULT_DATA_DIR / "fir_data.csv").exists():
            df = pd.read_csv(DEFAULT_DATA_DIR / "fir_data.csv")
        else:
            raise RuntimeError(f"Failed to load FIR dataset: {e}")

    # Column name normalization
    df.columns = [c.strip().lower() for c in df.columns]

    # Ensure all required columns exist with safe defaults
    for col in REQUIRED_FIR_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["fir_id"] = df["fir_id"].astype(str).str.strip()
    df["crime_type"] = df["crime_type"].fillna("Unknown").astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["location"] = df["location"].fillna("Unknown").astype(str).str.strip()
    df["persons"] = df["persons"].fillna("").astype(str)
    df["phone_numbers"] = df["phone_numbers"].fillna("").astype(str)

    # Parse timestamps safely
    df["date"] = pd.to_datetime(df["date"], errors="coerce").fillna(pd.Timestamp.now())

    return df


def load_cdr_data(source: Optional[Union[str, Path, Any]] = None) -> pd.DataFrame:
    """
    Loads Call Detail Records (CDR) dataset.
    """
    if source is None:
        source = DEFAULT_DATA_DIR / "cdr_data.csv"

    try:
        df = pd.read_csv(source)
    except Exception as e:
        if source != DEFAULT_DATA_DIR / "cdr_data.csv" and (DEFAULT_DATA_DIR / "cdr_data.csv").exists():
            df = pd.read_csv(DEFAULT_DATA_DIR / "cdr_data.csv")
        else:
            raise RuntimeError(f"Failed to load CDR dataset: {e}")

    df.columns = [c.strip().lower() for c in df.columns]

    for col in REQUIRED_CDR_COLUMNS:
        if col not in df.columns:
            df[col] = "" if "location" in col or "number" in col else 0

    df["caller_number"] = df["caller_number"].apply(clean_phone_str)
    df["receiver_number"] = df["receiver_number"].apply(clean_phone_str)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0).astype(int)
    df["tower_location"] = df["tower_location"].fillna("Unknown").astype(str).str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").fillna(pd.Timestamp.now())

    # Filter out empty records
    df = df[(df["caller_number"] != "") & (df["receiver_number"] != "")].copy()
    return df


def load_transaction_data(source: Optional[Union[str, Path, Any]] = None) -> pd.DataFrame:
    """
    Loads Financial Transactions dataset.
    """
    if source is None:
        source = DEFAULT_DATA_DIR / "transactions.csv"

    try:
        df = pd.read_csv(source)
    except Exception as e:
        if source != DEFAULT_DATA_DIR / "transactions.csv" and (DEFAULT_DATA_DIR / "transactions.csv").exists():
            df = pd.read_csv(DEFAULT_DATA_DIR / "transactions.csv")
        else:
            raise RuntimeError(f"Failed to load Transaction dataset: {e}")

    df.columns = [c.strip().lower() for c in df.columns]

    for col in REQUIRED_TXN_COLUMNS:
        if col not in df.columns:
            df[col] = "" if "id" in col or "location" in col else 0.0

    df["transaction_id"] = df["transaction_id"].astype(str).str.strip()
    df["sender_id"] = df["sender_id"].fillna("Unknown").astype(str).str.strip()
    df["receiver_id"] = df["receiver_id"].fillna("Unknown").astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["location"] = df["location"].fillna("Unknown").astype(str).str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").fillna(pd.Timestamp.now())

    df = df[(df["sender_id"] != "") & (df["receiver_id"] != "")].copy()
    return df


def load_all_datasets(fir_source=None, cdr_source=None, txn_source=None) -> Dict[str, pd.DataFrame]:
    """Loads all 3 core investigation datasets together."""
    return {
        "fir": load_fir_data(fir_source),
        "cdr": load_cdr_data(cdr_source),
        "transactions": load_transaction_data(txn_source),
    }
