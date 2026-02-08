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

from backend.core.config import CSV_PATH
from backend.core.geocoding import geocode_facility

# ── Columns that store JSON-encoded lists ────────────────────────────────────
JSON_LIST_COLS = [
    "specialties", "procedure", "equipment", "capability",
    "phone_numbers", "websites", "affiliationTypeIds", "countries",
]

FREE_TEXT_COLS = ["description", "organizationDescription", "missionStatement"]

METADATA_COLS = [
    "name", "pk_unique_id", "unique_id", "organization_type",
    "facilityTypeId", "operatorTypeId",
    "address_line1", "address_city", "address_stateOrRegion",
    "address_country", "address_countryCode",
    "source_url", "officialWebsite", "email",
    "yearEstablished", "numberDoctors", "capacity", "area",
    "latitude", "longitude",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_parse_json_list(value: Any) -> List[str]:
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, list):
        return value
    s = str(value).strip()
    if s in ("", "null", "[]", "None"):
        return []
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]
        return [str(parsed)]
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]
        return [str(parsed)]
    except (ValueError, SyntaxError):
        pass
    return [s]


def _camel_to_readable(name: str) -> str:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return spaced.replace("And", "and").title()


def _non_empty(value: Any) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, str) and value.strip() in ("", "null", "None", "[]"):
        return False
    return True


def _richness_score(row: pd.Series) -> int:
    return sum(1 for col in row.index if _non_empty(row[col]))


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────────────────────

def load_raw_data(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str)
    print(f"  Loaded {len(df)} rows x {len(df.columns)} columns from {csv_path.name}")
    return df


def clean_and_parse(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    df.replace({"null": pd.NA, "None": pd.NA, "": pd.NA}, inplace=True)
    for col in JSON_LIST_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_safe_parse_json_list)
    if "facilityTypeId" in df.columns:
        df["facilityTypeId"] = df["facilityTypeId"].replace({"farmacy": "pharmacy"})
    return df


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_richness"] = df.apply(_richness_score, axis=1)
    df.sort_values("_richness", ascending=False, inplace=True)
    grouped = df.groupby("pk_unique_id", sort=False)
    merged_rows: List[Dict] = []
    for pk, group in grouped:
        base = group.iloc[0].to_dict()
        for col in JSON_LIST_COLS:
            if col in df.columns:
                combined, seen = [], set()
                for _, row in group.iterrows():
                    for item in row[col]:
                        if item not in seen:
                            seen.add(item)
                            combined.append(item)
                base[col] = combined
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
    print(f"  Deduplicated: {len(df)} rows -> {len(result)} unique facilities/NGOs")
    return result


def build_documents(df: pd.DataFrame) -> pd.DataFrame:
    documents: List[str] = []
    metadata_list: List[Dict] = []

    for _, row in df.iterrows():
        parts: List[str] = []
        name = row.get("name", "Unknown Facility")
        org_type = row.get("organization_type", "facility")
        facility_type = row.get("facilityTypeId", "")
        parts.append(f"Name: {name}")
        parts.append(f"Type: {org_type}" + (f" ({facility_type})" if _non_empty(facility_type) else ""))

        loc_parts = []
        for col in ["address_line1", "address_line2", "address_city", "address_stateOrRegion", "address_country"]:
            v = row.get(col)
            if _non_empty(v):
                loc_parts.append(str(v))
        if loc_parts:
            parts.append(f"Location: {', '.join(loc_parts)}")

        specs = row.get("specialties", [])
        if specs:
            readable = [_camel_to_readable(s) for s in specs]
            parts.append(f"Medical Specialties: {', '.join(readable)}")

        procs = row.get("procedure", [])
        if procs:
            parts.append(f"Procedures: {'; '.join(procs)}")

        equip = row.get("equipment", [])
        if equip:
            parts.append(f"Equipment: {'; '.join(equip)}")

        caps = row.get("capability", [])
        if caps:
            parts.append(f"Capabilities: {'; '.join(caps)}")

        for col in FREE_TEXT_COLS:
            val = row.get(col)
            if _non_empty(val):
                parts.append(f"{col}: {val}")

        if _non_empty(row.get("operatorTypeId")):
            parts.append(f"Operator: {row['operatorTypeId']}")
        if _non_empty(row.get("numberDoctors")):
            parts.append(f"Number of Doctors: {row['numberDoctors']}")
        if _non_empty(row.get("capacity")):
            parts.append(f"Bed Capacity: {row['capacity']}")
        if _non_empty(row.get("yearEstablished")):
            parts.append(f"Year Established: {row['yearEstablished']}")

        doc_text = "\n".join(parts)
        documents.append(doc_text)

        meta: Dict[str, Any] = {}
        for col in METADATA_COLS:
            val = row.get(col)
            if _non_empty(val):
                meta[col] = val if not isinstance(val, float) else (int(val) if val == int(val) else val)
            else:
                meta[col] = None
        meta["specialties"] = row.get("specialties", [])
        meta["procedure"] = row.get("procedure", [])
        meta["equipment"] = row.get("equipment", [])
        meta["capability"] = row.get("capability", [])
        meta["affiliationTypeIds"] = row.get("affiliationTypeIds", [])

        # ── Geocode: enrich with lat/lng from city/region lookup ──
        if meta.get("latitude") is None or meta.get("longitude") is None:
            city = meta.get("address_city") or ""
            region = meta.get("address_stateOrRegion") or ""
            lat, lng = geocode_facility(city, region)
            if lat is not None and lng is not None:
                meta["latitude"] = lat
                meta["longitude"] = lng

        metadata_list.append(meta)

    df = df.copy()
    df["document"] = documents
    df["metadata"] = metadata_list
    geocoded = sum(1 for m in metadata_list if m.get("latitude") is not None)
    print(f"  Built {len(documents)} documents (avg {sum(len(d) for d in documents) // len(documents)} chars)")
    print(f"  Geocoded: {geocoded}/{len(metadata_list)} facilities have coordinates")
    return df


# ── Singleton cache so preprocessing only runs once ──────────────────────────
_preprocessing_cache: Optional[pd.DataFrame] = None


def run_preprocessing(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    global _preprocessing_cache
    if _preprocessing_cache is not None:
        return _preprocessing_cache.copy()

    print("--- Data Preprocessing Pipeline ---")
    df = load_raw_data(csv_path)
    df = clean_and_parse(df)
    df = deduplicate(df)
    df = build_documents(df)
    print("--- Preprocessing complete ---\n")

    _preprocessing_cache = df
    return df.copy()
