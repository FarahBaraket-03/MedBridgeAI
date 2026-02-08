"""
MedBridge AI — AGENT 2: Genie Chat (Text2SQL)
===============================================
Converts natural-language queries into Pandas operations over the
facility DataFrame, exposing a SQL-like trace for transparency.

Supports:
  - COUNT queries   ("how many hospitals have cardiology?")
  - FILTER queries  ("hospitals in Greater Accra with surgery")
  - AGGREGATE       ("which region has the most clinics?")
  - RATIO queries   ("bed-to-doctor ratios")
  - SINGLE POINT    ("procedures depending on very few facilities")
"""

import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.core.config import CSV_PATH, MEDICAL_SPECIALTIES_MAP
from backend.core.preprocessing import run_preprocessing


class GenieChatAgent:
    """Text2SQL agent operating on preprocessed facility DataFrame."""

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None:
            self._source_df = df
        else:
            self._source_df = run_preprocessing()
        self._build_flat_df()

    def _build_flat_df(self):
        """Flatten metadata into a queryable DataFrame."""
        rows = []
        for m in self._source_df["metadata"].tolist():
            rows.append({
                "name": m.get("name"),
                "pk_unique_id": m.get("pk_unique_id"),
                "unique_id": m.get("unique_id"),
                "organization_type": m.get("organization_type"),
                "facilityTypeId": m.get("facilityTypeId"),
                "address_city": m.get("address_city"),
                "address_stateOrRegion": m.get("address_stateOrRegion"),
                "yearEstablished": m.get("yearEstablished"),
                "numberDoctors": m.get("numberDoctors"),
                "capacity": m.get("capacity"),
                "area": m.get("area"),
                "latitude": m.get("latitude"),
                "longitude": m.get("longitude"),
                "source_url": m.get("source_url"),
                "specialties": m.get("specialties", []),
                "procedure": m.get("procedure", []),
                "equipment": m.get("equipment", []),
                "capability": m.get("capability", []),
            })
        self.flat_df = pd.DataFrame(rows)
        for col in ["yearEstablished", "numberDoctors", "capacity", "area", "latitude", "longitude"]:
            self.flat_df[col] = pd.to_numeric(self.flat_df[col], errors="coerce")

    # ── Extraction ───────────────────────────────────────────────────────────

    def _extract_specialty(self, query: str) -> Optional[str]:
        q = query.lower()
        for sid, kws in MEDICAL_SPECIALTIES_MAP.items():
            for kw in kws:
                if kw in q:
                    return sid
        return None

    def _extract_facility_type(self, query: str) -> Optional[str]:
        q = query.lower()
        for ft in ["hospital", "clinic", "pharmacy", "dentist"]:
            if ft in q:
                return ft
        return None

    def _extract_region(self, query: str) -> Optional[str]:
        q = query.lower()
        regions = [
            "Greater Accra", "Ashanti", "Western", "Eastern", "Central",
            "Northern", "Upper East", "Upper West", "Volta", "Bono",
            "Bono East", "Ahafo", "Savannah", "North East", "Oti",
        ]
        cities = [
            "Accra", "Kumasi", "Tamale", "Takoradi", "Cape Coast",
            "Sunyani", "Bolgatanga", "Wa", "Koforidua", "Tema", "Ho",
        ]
        for r in regions:
            if r.lower() in q:
                return r
        for c in cities:
            if re.search(r'\b' + re.escape(c.lower()) + r'\b', q):
                return c
        return None

    def _extract_procedure(self, query: str) -> Optional[str]:
        q = query.lower()
        kws = [
            "cataract", "surgery", "cesarean", "dialysis", "chemotherapy",
            "endoscopy", "ultrasound", "x-ray", "mri", "ct scan",
            "blood transfusion", "dental", "physiotherapy",
        ]
        for kw in kws:
            if kw in q:
                return kw
        return None

    # ── Query handlers ───────────────────────────────────────────────────────

    def _is_negated(self, query: str) -> bool:
        """Detect negation intent so filters can be inverted.

        Catches patterns like 'facilities that do NOT have cardiology',
        'hospitals without MRI', 'clinics that don't offer surgery'.
        """
        return bool(re.search(
            r"\b(not|without|don.t|doesn.t|don't|doesn't|no\s+\w+|lack|missing|absent)\b",
            query.lower(),
        ))

    def count_with_specialty(self, specialty: str, facility_type: Optional[str] = None,
                             negated: bool = False) -> Dict:
        mask = self.flat_df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)
        if negated:
            mask = ~mask  # invert: facilities WITHOUT this specialty
        if facility_type:
            mask &= self.flat_df["facilityTypeId"].str.lower().fillna("") == facility_type.lower()
        matched = self.flat_df[mask]
        neg_word = "NOT " if negated else ""
        sql = f"SELECT COUNT(*) FROM facilities WHERE '{specialty}' {neg_word}IN specialties"
        if facility_type:
            sql += f" AND facilityTypeId = '{facility_type}'"
        return {
            "sql": sql, "count": len(matched),
            "facilities": matched[["name", "address_city", "address_stateOrRegion", "facilityTypeId", "specialties", "latitude", "longitude"]].to_dict("records"),
            "citations": [{"pk_unique_id": r.get("pk_unique_id"), "field": "specialties"} for r in matched[["pk_unique_id"]].to_dict("records")],
        }

    def facilities_in_region(self, region: str, specialty: Optional[str] = None,
                             procedure: Optional[str] = None, facility_type: Optional[str] = None) -> Dict:
        rl = region.lower()
        mask = (
            self.flat_df["address_city"].fillna("").str.lower().str.contains(rl)
            | self.flat_df["address_stateOrRegion"].fillna("").str.lower().str.contains(rl)
        )
        if specialty:
            mask &= self.flat_df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)
        if procedure:
            mask &= self.flat_df["procedure"].apply(lambda ps: isinstance(ps, list) and any(procedure.lower() in p.lower() for p in ps))
        if facility_type:
            mask &= self.flat_df["facilityTypeId"].str.lower().fillna("") == facility_type.lower()
        matched = self.flat_df[mask]
        sql = f"SELECT * FROM facilities WHERE region LIKE '%{region}%'"
        if specialty:
            sql += f" AND '{specialty}' IN specialties"
        if procedure:
            sql += f" AND procedure LIKE '%{procedure}%'"
        return {
            "sql": sql, "count": len(matched),
            "facilities": matched[["name", "address_city", "address_stateOrRegion", "facilityTypeId", "specialties", "latitude", "longitude"]].to_dict("records"),
        }

    def region_aggregation(self, facility_type: Optional[str] = None) -> Dict:
        df = self.flat_df.copy()
        if facility_type:
            df = df[df["facilityTypeId"].str.lower().fillna("") == facility_type.lower()]
        counts = df["address_stateOrRegion"].fillna("Unknown").value_counts()
        sql = "SELECT address_stateOrRegion, COUNT(*) FROM facilities"
        if facility_type:
            sql += f" WHERE facilityTypeId = '{facility_type}'"
        sql += " GROUP BY address_stateOrRegion ORDER BY count DESC"
        return {
            "sql": sql, "aggregation": counts.to_dict(),
            "top_region": counts.index[0] if len(counts) > 0 else None,
            "top_count": int(counts.iloc[0]) if len(counts) > 0 else 0,
        }

    def specialty_distribution(self) -> Dict:
        all_specs = []
        for s in self.flat_df["specialties"]:
            all_specs.extend(s)
        counts = Counter(all_specs)
        return {
            "sql": "SELECT specialty, COUNT(*) FROM facility_specialties GROUP BY specialty ORDER BY count DESC",
            "distribution": dict(counts.most_common(30)),
            "total_unique_specialties": len(counts),
        }

    def facilities_with_procedure(self, procedure: str, region: Optional[str] = None) -> Dict:
        mask = self.flat_df["procedure"].apply(lambda ps: isinstance(ps, list) and any(procedure.lower() in p.lower() for p in ps))
        mask |= self.flat_df["capability"].apply(lambda cs: isinstance(cs, list) and any(procedure.lower() in c.lower() for c in cs))
        if region:
            rl = region.lower()
            mask &= (
                self.flat_df["address_city"].fillna("").str.lower().str.contains(rl)
                | self.flat_df["address_stateOrRegion"].fillna("").str.lower().str.contains(rl)
            )
        matched = self.flat_df[mask]
        return {
            "sql": f"SELECT * FROM facilities WHERE procedure LIKE '%{procedure}%'",
            "count": len(matched),
            "facilities": matched[["name", "address_city", "address_stateOrRegion", "procedure", "capability", "specialties", "latitude", "longitude"]].to_dict("records"),
        }

    def anomaly_bed_doctor_ratio(self) -> Dict:
        df = self.flat_df.dropna(subset=["capacity", "numberDoctors"])
        df = df[(df["capacity"] > 0) & (df["numberDoctors"] > 0)].copy()

        if df.empty:
            return {
                "sql": "SELECT *, capacity/numberDoctors AS ratio FROM facilities -- no valid rows",
                "count": 0,
                "anomalies": [],
                "avg_ratio": None,
                "threshold": None,
                "iqr_stats": {},
            }

        df["bed_to_doctor"] = df["capacity"] / df["numberDoctors"]

        # IQR-based outlier detection instead of a hardcoded threshold.
        # Adapts to the actual data distribution so it works correctly
        # regardless of whether the dataset is mostly rural clinics
        # (median ~10) or teaching hospitals (median ~30).
        q25 = df["bed_to_doctor"].quantile(0.25)
        q75 = df["bed_to_doctor"].quantile(0.75)
        iqr = q75 - q25
        upper_fence = q75 + 1.5 * iqr
        threshold = max(upper_fence, 20.0)  # never below 20 to avoid noise

        anomalies = df[df["bed_to_doctor"] > threshold]
        return {
            "sql": f"SELECT *, capacity/numberDoctors AS ratio FROM facilities WHERE ratio > {threshold:.1f} (IQR-derived)",
            "count": len(anomalies),
            "anomalies": anomalies[["name", "capacity", "numberDoctors", "bed_to_doctor"]].to_dict("records"),
            "avg_ratio": round(df["bed_to_doctor"].mean(), 1) if len(df) > 0 else None,
            "threshold": round(threshold, 1),
            "iqr_stats": {"q25": round(q25, 1), "q75": round(q75, 1), "iqr": round(iqr, 1)},
        }

    def single_point_of_failure(self) -> Dict:
        all_specs = []
        for s in self.flat_df["specialties"]:
            all_specs.extend(s)
        counts = Counter(all_specs)
        rare = {k: v for k, v in counts.items() if v <= 2}
        return {
            "sql": "SELECT specialty, COUNT(*) FROM facility_specialties GROUP BY specialty HAVING cnt <= 2",
            "rare_specialties": rare, "count": len(rare),
        }

    # ── Main dispatcher ──────────────────────────────────────────────────────

    def execute_query(self, query: str) -> Dict:
        t0 = time.time()
        specialty = self._extract_specialty(query)
        ftype = self._extract_facility_type(query)
        region = self._extract_region(query)
        procedure = self._extract_procedure(query)
        negated = self._is_negated(query)
        ql = query.lower()

        if re.search(r"how many|count|number of", ql):
            if specialty:
                result = self.count_with_specialty(specialty, ftype, negated=negated)
            elif procedure:
                result = self.facilities_with_procedure(procedure, region)
            elif region:
                result = self.facilities_in_region(region, facility_type=ftype)
            else:
                df = self.flat_df
                if ftype:
                    df = df[df["facilityTypeId"].str.lower().fillna("") == ftype.lower()]
                result = {"sql": "SELECT COUNT(*) FROM facilities", "count": len(df)}

        elif re.search(r"which region|most .*(hospital|clinic)|region.*most", ql):
            result = self.region_aggregation(ftype)

        elif re.search(r"distribution|breakdown|by (region|city|specialty)", ql):
            if "specialty" in ql or "specialties" in ql:
                result = self.specialty_distribution()
            else:
                result = self.region_aggregation(ftype)

        elif re.search(r"bed.to.doctor|ratio|anomal", ql):
            result = self.anomaly_bed_doctor_ratio()

        elif re.search(r"single point|few facilit|rare|depend", ql):
            result = self.single_point_of_failure()

        elif specialty or procedure:
            if procedure:
                result = self.facilities_with_procedure(procedure, region)
            else:
                result = self.count_with_specialty(specialty, ftype)

        elif region:
            result = self.facilities_in_region(region, specialty, procedure, ftype)

        else:
            result = {
                "sql": "SELECT overview FROM facilities",
                "total_facilities": len(self.flat_df[self.flat_df["organization_type"] == "facility"]),
                "total_ngos": len(self.flat_df[self.flat_df["organization_type"] == "ngo"]),
                "facility_types": self.flat_df["facilityTypeId"].value_counts().to_dict(),
            }

        result["query"] = query
        result["duration_ms"] = round((time.time() - t0) * 1000, 2)
        result["agent"] = "genie"
        if "action" not in result:
            result["action"] = "text2sql"
        return result
