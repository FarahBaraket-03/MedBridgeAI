"""
MedBridge AI — Genie Chat Agent (Text2SQL)
============================================
Converts natural-language queries into structured filters over the
facility DataFrame. Since we have a flat CSV (not a real SQL DB),
this agent translates queries into Pandas operations but exposes
a SQL-like interface for transparency and tracing.

Supports:
  - COUNT queries  ("how many hospitals have cardiology?")
  - FILTER queries ("hospitals in Greater Accra with surgery")
  - AGGREGATE queries ("which region has the most clinics?")
  - RATIO queries ("bed-to-doctor ratios")
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config import CSV_PATH
from src.data_preprocessing import run_preprocessing


class GenieChatAgent:
    """
    Text2SQL-style agent that operates on the preprocessed DataFrame.
    Generates a pseudo-SQL query for tracing, then executes it as Pandas.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None:
            self.df = df
        else:
            self.df = run_preprocessing()
        self._build_indexes()

    def _build_indexes(self):
        """Pre-compute lookup structures for fast querying."""
        meta = self.df["metadata"].tolist()

        # Flatten into a queryable DataFrame
        rows = []
        for m in meta:
            row = {
                "name": m.get("name"),
                "pk_unique_id": m.get("pk_unique_id"),
                "unique_id": m.get("unique_id"),
                "organization_type": m.get("organization_type"),
                "facilityTypeId": m.get("facilityTypeId"),
                "operatorTypeId": m.get("operatorTypeId"),
                "address_city": m.get("address_city"),
                "address_stateOrRegion": m.get("address_stateOrRegion"),
                "address_country": m.get("address_country"),
                "yearEstablished": m.get("yearEstablished"),
                "numberDoctors": m.get("numberDoctors"),
                "capacity": m.get("capacity"),
                "area": m.get("area"),
                "source_url": m.get("source_url"),
                "specialties": m.get("specialties", []),
                "procedure": m.get("procedure", []),
                "equipment": m.get("equipment", []),
                "capability": m.get("capability", []),
            }
            rows.append(row)

        self.flat_df = pd.DataFrame(rows)

        # Convert numeric columns
        for col in ["yearEstablished", "numberDoctors", "capacity", "area"]:
            self.flat_df[col] = pd.to_numeric(self.flat_df[col], errors="coerce")

    # ── Query parsing ────────────────────────────────────────────────────────

    def _extract_specialty(self, query: str) -> Optional[str]:
        """Extract a medical specialty keyword from the query."""
        from src.config import MEDICAL_SPECIALTIES_MAP

        query_lower = query.lower()
        for specialty_id, keywords in MEDICAL_SPECIALTIES_MAP.items():
            for kw in keywords:
                if kw in query_lower:
                    return specialty_id
        return None

    def _extract_facility_type(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        for ftype in ["hospital", "clinic", "pharmacy", "dentist", "doctor"]:
            if ftype in query_lower:
                return ftype
        return None

    def _extract_region(self, query: str) -> Optional[str]:
        """Extract a region/city name from the query."""
        # Known Ghana regions
        regions = [
            "Greater Accra", "Ashanti", "Western", "Eastern", "Central",
            "Northern", "Upper East", "Upper West", "Volta", "Bono",
            "Bono East", "Ahafo", "Savannah", "North East", "Oti",
            "Western North",
        ]
        cities = [
            "Accra", "Kumasi", "Tamale", "Takoradi", "Cape Coast",
            "Ho", "Sunyani", "Bolgatanga", "Wa", "Koforidua",
            "Tema", "Obuasi", "Techiman",
        ]
        query_lower = query.lower()
        for r in regions:
            if r.lower() in query_lower:
                return r
        for c in cities:
            if c.lower() in query_lower:
                return c
        return None

    def _extract_procedure_keyword(self, query: str) -> Optional[str]:
        """Extract a procedure-related keyword from the query."""
        keywords = [
            "surgery", "cataract", "cesarean", "dialysis", "chemotherapy",
            "endoscopy", "ultrasound", "x-ray", "mri", "ct scan",
            "vaccination", "immunization", "blood transfusion",
            "dental", "physiotherapy", "radiology",
        ]
        query_lower = query.lower()
        for kw in keywords:
            if kw in query_lower:
                return kw
        return None

    # ── Query execution ──────────────────────────────────────────────────────

    def count_facilities_with_specialty(self, specialty: str, facility_type: Optional[str] = None) -> Dict:
        """COUNT query: how many facilities have a given specialty."""
        mask = self.flat_df["specialties"].apply(lambda specs: specialty in specs)
        if facility_type:
            mask &= self.flat_df["facilityTypeId"] == facility_type

        matched = self.flat_df[mask]
        sql = f"SELECT COUNT(*) FROM facilities WHERE '{specialty}' IN specialties"
        if facility_type:
            sql += f" AND facilityTypeId = '{facility_type}'"

        return {
            "sql": sql,
            "count": len(matched),
            "facilities": matched[["name", "address_city", "facilityTypeId"]].to_dict("records"),
        }

    def facilities_in_region(
        self,
        region: str,
        specialty: Optional[str] = None,
        procedure_keyword: Optional[str] = None,
        facility_type: Optional[str] = None,
    ) -> Dict:
        """FILTER query: facilities in a region with optional specialty/procedure filter."""
        region_lower = region.lower()
        mask = (
            self.flat_df["address_city"].fillna("").str.lower().str.contains(region_lower)
            | self.flat_df["address_stateOrRegion"].fillna("").str.lower().str.contains(region_lower)
        )

        if specialty:
            mask &= self.flat_df["specialties"].apply(lambda s: specialty in s)
        if procedure_keyword:
            mask &= self.flat_df["procedure"].apply(
                lambda procs: any(procedure_keyword.lower() in p.lower() for p in procs)
            )
        if facility_type:
            mask &= self.flat_df["facilityTypeId"] == facility_type

        matched = self.flat_df[mask]

        sql = f"SELECT * FROM facilities WHERE region LIKE '%{region}%'"
        if specialty:
            sql += f" AND '{specialty}' IN specialties"
        if procedure_keyword:
            sql += f" AND procedure LIKE '%{procedure_keyword}%'"

        return {
            "sql": sql,
            "count": len(matched),
            "facilities": matched[["name", "address_city", "address_stateOrRegion", "facilityTypeId", "specialties"]].to_dict("records"),
        }

    def region_aggregation(self, facility_type: Optional[str] = None) -> Dict:
        """AGGREGATE: count facilities per region."""
        df = self.flat_df.copy()
        if facility_type:
            df = df[df["facilityTypeId"] == facility_type]

        counts = df["address_stateOrRegion"].fillna("Unknown").value_counts()

        sql = "SELECT address_stateOrRegion, COUNT(*) FROM facilities"
        if facility_type:
            sql += f" WHERE facilityTypeId = '{facility_type}'"
        sql += " GROUP BY address_stateOrRegion ORDER BY count DESC"

        return {
            "sql": sql,
            "aggregation": counts.to_dict(),
            "top_region": counts.index[0] if len(counts) > 0 else None,
            "top_count": int(counts.iloc[0]) if len(counts) > 0 else 0,
        }

    def city_aggregation(self, facility_type: Optional[str] = None) -> Dict:
        """AGGREGATE: count facilities per city."""
        df = self.flat_df.copy()
        if facility_type:
            df = df[df["facilityTypeId"] == facility_type]

        counts = df["address_city"].fillna("Unknown").value_counts()

        sql = "SELECT address_city, COUNT(*) FROM facilities"
        if facility_type:
            sql += f" WHERE facilityTypeId = '{facility_type}'"
        sql += " GROUP BY address_city ORDER BY count DESC"

        return {
            "sql": sql,
            "aggregation": counts.head(20).to_dict(),
        }

    def specialty_distribution(self) -> Dict:
        """AGGREGATE: count facilities per specialty."""
        from collections import Counter
        all_specs = []
        for specs in self.flat_df["specialties"]:
            all_specs.extend(specs)
        counts = Counter(all_specs)

        return {
            "sql": "SELECT specialty, COUNT(*) FROM facility_specialties GROUP BY specialty ORDER BY count DESC",
            "distribution": dict(counts.most_common(30)),
            "total_unique_specialties": len(counts),
        }

    def facilities_with_procedure(self, procedure_keyword: str, region: Optional[str] = None) -> Dict:
        """Find facilities that perform a specific procedure."""
        mask = self.flat_df["procedure"].apply(
            lambda procs: any(procedure_keyword.lower() in p.lower() for p in procs)
        )
        # Also search in capability text
        mask |= self.flat_df["capability"].apply(
            lambda caps: any(procedure_keyword.lower() in c.lower() for c in caps)
        )

        if region:
            region_lower = region.lower()
            mask &= (
                self.flat_df["address_city"].fillna("").str.lower().str.contains(region_lower)
                | self.flat_df["address_stateOrRegion"].fillna("").str.lower().str.contains(region_lower)
            )

        matched = self.flat_df[mask]

        sql = f"SELECT * FROM facilities WHERE capability LIKE '%{procedure_keyword}%'"
        if region:
            sql += f" AND region LIKE '%{region}%'"

        return {
            "sql": sql,
            "count": len(matched),
            "facilities": matched[["name", "address_city", "address_stateOrRegion", "procedure", "capability"]].to_dict("records"),
        }

    def anomaly_bed_doctor_ratio(self) -> Dict:
        """Find facilities with unusual bed-to-doctor ratios."""
        df = self.flat_df.dropna(subset=["capacity", "numberDoctors"])
        df = df[(df["capacity"] > 0) & (df["numberDoctors"] > 0)].copy()
        df["bed_to_doctor"] = df["capacity"] / df["numberDoctors"]

        anomalies = df[df["bed_to_doctor"] > 50]  # More than 50 beds per doctor

        return {
            "sql": "SELECT *, capacity/numberDoctors AS ratio FROM facilities WHERE ratio > 50",
            "count": len(anomalies),
            "anomalies": anomalies[["name", "capacity", "numberDoctors", "bed_to_doctor"]].to_dict("records"),
            "avg_ratio": round(df["bed_to_doctor"].mean(), 1) if len(df) > 0 else None,
        }

    def single_point_of_failure(self) -> Dict:
        """Find procedures/specialties offered by very few facilities (<=2)."""
        from collections import Counter
        all_specs = []
        for specs in self.flat_df["specialties"]:
            all_specs.extend(specs)
        counts = Counter(all_specs)

        rare = {k: v for k, v in counts.items() if v <= 2}

        return {
            "sql": "SELECT specialty, COUNT(*) as cnt FROM facility_specialties GROUP BY specialty HAVING cnt <= 2",
            "rare_specialties": rare,
            "count": len(rare),
        }

    # ── High-level query dispatcher ──────────────────────────────────────────

    def execute_query(self, query: str) -> Dict:
        """
        Parse a natural language query and execute the appropriate operation.
        Returns result dict with 'sql', 'count'/'aggregation', and data.
        """
        t0 = time.time()

        specialty = self._extract_specialty(query)
        facility_type = self._extract_facility_type(query)
        region = self._extract_region(query)
        procedure = self._extract_procedure_keyword(query)

        query_lower = query.lower()

        # Route to appropriate handler
        if re.search(r"how many|count|number of", query_lower):
            if specialty:
                result = self.count_facilities_with_specialty(specialty, facility_type)
            elif procedure:
                result = self.facilities_with_procedure(procedure, region)
            elif region:
                result = self.facilities_in_region(region, facility_type=facility_type)
            else:
                # General count
                df = self.flat_df
                if facility_type:
                    df = df[df["facilityTypeId"] == facility_type]
                result = {"sql": "SELECT COUNT(*) FROM facilities", "count": len(df)}

        elif re.search(r"which region|most .*(hospital|clinic)|region.*most", query_lower):
            result = self.region_aggregation(facility_type)

        elif re.search(r"distribution|breakdown|by (region|city|specialty)", query_lower):
            if "specialty" in query_lower or "specialties" in query_lower:
                result = self.specialty_distribution()
            elif "city" in query_lower:
                result = self.city_aggregation(facility_type)
            else:
                result = self.region_aggregation(facility_type)

        elif re.search(r"bed.to.doctor|ratio|anomal", query_lower):
            result = self.anomaly_bed_doctor_ratio()

        elif re.search(r"single point|few facilit|rare|depend", query_lower):
            result = self.single_point_of_failure()

        elif specialty or procedure:
            if procedure:
                result = self.facilities_with_procedure(procedure, region)
            else:
                result = self.count_facilities_with_specialty(specialty, facility_type)

        elif region:
            result = self.facilities_in_region(region, specialty, procedure, facility_type)

        else:
            # Fallback: return general stats
            result = {
                "sql": "SELECT * FROM facilities LIMIT 10",
                "total_facilities": len(self.flat_df[self.flat_df["organization_type"] == "facility"]),
                "total_ngos": len(self.flat_df[self.flat_df["organization_type"] == "ngo"]),
                "facility_types": self.flat_df["facilityTypeId"].value_counts().to_dict(),
            }

        duration = (time.time() - t0) * 1000
        result["query"] = query
        result["duration_ms"] = round(duration, 2)
        return result


def create_genie_agent(df: Optional[pd.DataFrame] = None) -> GenieChatAgent:
    return GenieChatAgent(df)


if __name__ == "__main__":
    agent = create_genie_agent()

    test_queries = [
        "How many hospitals have cardiology?",
        "How many hospitals in Accra can perform surgery?",
        "Which region has the most hospitals?",
        "Facilities with cataract surgery",
        "Bed to doctor ratio anomalies",
        "Specialties depending on very few facilities",
        "Distribution of specialties",
    ]

    print("═══ Genie Chat Agent — Text2SQL Demo ═══\n")
    for q in test_queries:
        result = agent.execute_query(q)
        print(f"Q: {q}")
        print(f"  SQL: {result.get('sql', 'N/A')}")
        if "count" in result:
            print(f"  Result: {result['count']} facilities")
        elif "aggregation" in result:
            top_items = list(result["aggregation"].items())[:5]
            print(f"  Top: {top_items}")
        elif "rare_specialties" in result:
            print(f"  Rare: {list(result['rare_specialties'].keys())[:5]}")
        print(f"  Duration: {result.get('duration_ms', 0)}ms\n")
