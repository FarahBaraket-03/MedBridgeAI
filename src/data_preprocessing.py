"""
MedBridge AI — Data Preprocessing Pipeline
============================================
Loads the Virtue Foundation Ghana CSV, cleans it, parses JSON-encoded columns,
deduplicates by pk_unique_id (keeping the richest row), and builds a
composite text document per facility/NGO for downstream embedding.
"""

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "Virtue Foundation Ghana v0.3 - Sheet1.csv"

# ── Columns that store JSON-encoded lists ────────────────────────────────────
JSON_LIST_COLS = [
    "specialties",
    "procedure",
    "equipment",
    "capability",
    "phone_numbers",
    "websites",
    "affiliationTypeIds",
    "countries",
]

# ── Free-text columns that form the "document" for each facility ─────────────
FREE_TEXT_COLS = ["description", "organizationDescription", "missionStatement"]

# ── Structured metadata columns to keep alongside the document ───────────────
METADATA_COLS = [
    "name",
    "pk_unique_id",
    "unique_id",
    "organization_type",
    "facilityTypeId",
    "operatorTypeId",
    "address_line1",
    "address_city",
    "address_stateOrRegion",
    "address_country",
    "address_countryCode",
    "source_url",
    "officialWebsite",
    "email",
    "yearEstablished",
    "numberDoctors",
    "capacity",
    "area",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _safe_parse_json_list(value: Any) -> List[str]:
    """Parse a JSON-encoded list string into a Python list, gracefully."""
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, list):
        return value
    s = str(value).strip()
    if s in ("", "null", "[]", "None"):
        return []
    # Try JSON first
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]
        return [str(parsed)]
    except (json.JSONDecodeError, ValueError):
        pass
    # Fall back to ast.literal_eval
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]
        return [str(parsed)]
    except (ValueError, SyntaxError):
        pass
    # Last resort: treat as single value
    return [s]


def _camel_to_readable(name: str) -> str:
    """Convert camelCase specialty names to readable form.
    e.g. 'gynecologyAndObstetrics' -> 'Gynecology And Obstetrics'
    """
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return spaced.replace("And", "and").title()


def _non_empty(value: Any) -> bool:
    """Check if a value is non-empty / non-null."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, str) and value.strip() in ("", "null", "None", "[]"):
        return False
    return True


def _richness_score(row: pd.Series) -> int:
    """Score how 'information-rich' a row is (for dedup tie-breaking)."""
    score = 0
    for col in row.index:
        if _non_empty(row[col]):
            score += 1
    return score


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────────────────────


def load_raw_data(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """Load raw CSV.  Returns a DataFrame with all original columns."""
    df = pd.read_csv(csv_path, dtype=str)  # keep everything as str initially
    print(f"  Loaded {len(df)} rows × {len(df.columns)} columns from {csv_path.name}")
    return df


def clean_and_parse(df: pd.DataFrame) -> pd.DataFrame:
    """
    1. Strip whitespace from column names & string cells.
    2. Parse JSON-list columns into real Python lists.
    3. Fix known data issues (e.g. 'farmacy' -> 'pharmacy').
    """
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Strip whitespace in string cells
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # Replace explicit 'null'/'None' strings with real NaN
    df.replace({"null": pd.NA, "None": pd.NA, "": pd.NA}, inplace=True)

    # Parse JSON list columns
    for col in JSON_LIST_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_safe_parse_json_list)

    # Fix typos
    if "facilityTypeId" in df.columns:
        df["facilityTypeId"] = df["facilityTypeId"].replace({"farmacy": "pharmacy"})

    return df


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Multiple rows can share the same pk_unique_id (same facility scraped from
    different pages).  We merge them:
      - Lists are unioned (specialties, capability, …)
      - Scalar values: keep the first non-null.
    """
    df = df.copy()
    df["_richness"] = df.apply(_richness_score, axis=1)
    df.sort_values("_richness", ascending=False, inplace=True)

    grouped = df.groupby("pk_unique_id", sort=False)

    merged_rows: List[Dict] = []
    for pk, group in grouped:
        base = group.iloc[0].to_dict()
        # Merge list columns via union
        for col in JSON_LIST_COLS:
            if col in df.columns:
                combined: List[str] = []
                seen = set()
                for _, row in group.iterrows():
                    for item in row[col]:
                        if item not in seen:
                            seen.add(item)
                            combined.append(item)
                base[col] = combined

        # Merge scalar columns: keep first non-null
        for col in df.columns:
            if col in JSON_LIST_COLS or col == "_richness":
                continue
            if not _non_empty(base.get(col)):
                for _, row in group.iterrows():
                    if _non_empty(row[col]):
                        base[col] = row[col]
                        break

        merged_rows.append(base)

    result = pd.DataFrame(merged_rows)
    result.drop(columns=["_richness"], inplace=True, errors="ignore")
    print(f"  Deduplicated: {len(df)} rows → {len(result)} unique facilities/NGOs")
    return result


def build_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compose a rich text **document** per facility for embedding.
    Also store structured metadata as a separate dict column.
    """
    documents: List[str] = []
    metadata_list: List[Dict] = []

    for _, row in df.iterrows():
        parts: List[str] = []

        # ── Header ──
        name = row.get("name", "Unknown Facility")
        org_type = row.get("organization_type", "facility")
        facility_type = row.get("facilityTypeId", "")
        parts.append(f"Name: {name}")
        parts.append(f"Type: {org_type}" + (f" ({facility_type})" if _non_empty(facility_type) else ""))

        # ── Location ──
        loc_parts = []
        for col in ["address_line1", "address_line2", "address_city", "address_stateOrRegion", "address_country"]:
            v = row.get(col)
            if _non_empty(v):
                loc_parts.append(str(v))
        if loc_parts:
            parts.append(f"Location: {', '.join(loc_parts)}")

        # ── Specialties ──
        specs = row.get("specialties", [])
        if specs:
            readable = [_camel_to_readable(s) for s in specs]
            parts.append(f"Medical Specialties: {', '.join(readable)}")

        # ── Procedures ──
        procs = row.get("procedure", [])
        if procs:
            parts.append(f"Procedures: {'; '.join(procs)}")

        # ── Equipment ──
        equip = row.get("equipment", [])
        if equip:
            parts.append(f"Equipment: {'; '.join(equip)}")

        # ── Capabilities ──
        caps = row.get("capability", [])
        if caps:
            parts.append(f"Capabilities: {'; '.join(caps)}")

        # ── Description / mission ──
        for col in FREE_TEXT_COLS:
            val = row.get(col)
            if _non_empty(val):
                parts.append(f"{col}: {val}")

        # ── Operational details ──
        if _non_empty(row.get("operatorTypeId")):
            parts.append(f"Operator: {row['operatorTypeId']}")
        if _non_empty(row.get("numberDoctors")):
            parts.append(f"Number of Doctors: {row['numberDoctors']}")
        if _non_empty(row.get("capacity")):
            parts.append(f"Bed Capacity: {row['capacity']}")
        if _non_empty(row.get("yearEstablished")):
            parts.append(f"Year Established: {row['yearEstablished']}")

        # Build document string
        doc_text = "\n".join(parts)
        documents.append(doc_text)

        # Build metadata dict (for Qdrant payload)
        meta: Dict[str, Any] = {}
        for col in METADATA_COLS:
            val = row.get(col)
            if _non_empty(val):
                meta[col] = val if not isinstance(val, float) else (int(val) if val == int(val) else val)
            else:
                meta[col] = None

        # Also store list fields in metadata for filtering
        meta["specialties"] = row.get("specialties", [])
        meta["procedure"] = row.get("procedure", [])
        meta["equipment"] = row.get("equipment", [])
        meta["capability"] = row.get("capability", [])
        meta["affiliationTypeIds"] = row.get("affiliationTypeIds", [])

        metadata_list.append(meta)

    df = df.copy()
    df["document"] = documents
    df["metadata"] = metadata_list

    print(f"  Built {len(documents)} documents (avg {sum(len(d) for d in documents)//len(documents)} chars)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────


def run_preprocessing(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """Full pipeline: load → clean → dedup → build documents."""
    print("─── Data Preprocessing Pipeline ───")
    df = load_raw_data(csv_path)
    df = clean_and_parse(df)
    df = deduplicate(df)
    df = build_documents(df)
    print("─── Preprocessing complete ───\n")
    return df


if __name__ == "__main__":
    df = run_preprocessing()
    # Quick sanity check
    print("Sample document (first facility):\n")
    print(df.iloc[0]["document"])
    print("\n--- metadata keys:", list(df.iloc[0]["metadata"].keys()))
