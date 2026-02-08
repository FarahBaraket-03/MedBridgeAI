"""
MedBridge AI — AGENT 4: Medical Reasoning (The Validator)
==========================================================
Validates facility claims using medical domain knowledge:
  1. Rule-based constraint validation (deterministic)
  2. Statistical anomaly detection (Isolation Forest)
  3. Language pattern analysis (red flags)

INPUT:  Facility data (structured + unstructured)
OUTPUT: Validation results with confidence scores and citations
"""

import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

try:
    from rapidfuzz import fuzz as _fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False

from backend.core.config import (
    ADVANCED_PROCEDURE_REQUIREMENTS,
    MEDICAL_SPECIALTIES_MAP,
    RED_FLAG_PATTERNS,
)
from backend.core.geocoding import geocode_facility
from backend.core.preprocessing import run_preprocessing


class MedicalReasoningAgent:
    """
    Hybrid medical reasoning agent combining:
      - Rule-based constraint checking
      - Isolation Forest anomaly detection
      - NLP red-flag pattern matching
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None:
            self._source_df = df
        else:
            self._source_df = run_preprocessing()
        self._build_flat_df()
        self._anomaly_model = None

    def _build_flat_df(self):
        rows = []
        for i, m in enumerate(self._source_df["metadata"].tolist()):
            doc = self._source_df.iloc[i].get("document", "")
            rows.append({
                "name": m.get("name", "Unknown"),
                "pk_unique_id": m.get("pk_unique_id"),
                "unique_id": m.get("unique_id"),
                "organization_type": m.get("organization_type"),
                "facilityTypeId": m.get("facilityTypeId"),
                "address_city": m.get("address_city"),
                "address_stateOrRegion": m.get("address_stateOrRegion"),
                "numberDoctors": m.get("numberDoctors"),
                "capacity": m.get("capacity"),
                "latitude": m.get("latitude"),
                "longitude": m.get("longitude"),
                "specialties": m.get("specialties", []),
                "procedure": m.get("procedure", []),
                "equipment": m.get("equipment", []),
                "capability": m.get("capability", []),
                "document_text": doc,
                "num_specialties": len(m.get("specialties", [])),
                "num_procedures": len(m.get("procedure", [])),
                "num_equipment": len(m.get("equipment", [])),
                "num_capabilities": len(m.get("capability", [])),
            })
        self.flat_df = pd.DataFrame(rows)
        for col in ["numberDoctors", "capacity", "latitude", "longitude"]:
            self.flat_df[col] = pd.to_numeric(self.flat_df[col], errors="coerce")

    # ═══════════════════════════════════════════════════════════════════════════
    #  1. CONSTRAINT VALIDATION (Rule-Based)
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_facility(self, facility_row: pd.Series) -> Dict:
        """
        Validate a single facility's claims against medical constraints.
        Returns validation result with confidence score.
        """
        issues = []
        name = facility_row.get("name", "Unknown")
        specialties = facility_row.get("specialties", []) or []
        procedures = facility_row.get("procedure", []) or []
        equipment = facility_row.get("equipment", []) or []
        capabilities = facility_row.get("capability", []) or []
        capacity = facility_row.get("capacity")
        doc_text = facility_row.get("document_text", "")

        # Combine all text for pattern matching
        all_text = " ".join([
            " ".join(procedures), " ".join(equipment), " ".join(capabilities), doc_text
        ]).lower()

        # Check each specialty against requirements
        for spec in specialties:
            for proc_key, reqs in ADVANCED_PROCEDURE_REQUIREMENTS.items():
                # Map specialty to procedure requirement
                if not self._specialty_matches_procedure(spec, proc_key):
                    continue

                # Check required equipment (fuzzy matching)
                for req_equip in reqs.get("required_equipment", []):
                    if not self._fuzzy_text_match(req_equip, all_text):
                        issues.append({
                            "type": "missing_equipment",
                            "severity": "high",
                            "specialty": spec,
                            "requirement": req_equip,
                            "message": f"Claims '{spec}' but no mention of required '{req_equip}'",
                        })

                # Check minimum beds
                min_beds = reqs.get("min_beds", 0)
                if capacity is not None and not pd.isna(capacity) and capacity < min_beds:
                    issues.append({
                        "type": "insufficient_capacity",
                        "severity": "medium",
                        "specialty": spec,
                        "requirement": f"min {min_beds} beds",
                        "actual": capacity,
                        "message": f"Claims '{spec}' but only {int(capacity)} beds (need {min_beds}+)",
                    })

                # Check required capabilities (fuzzy matching)
                for req_cap in reqs.get("required_capability", []):
                    if not self._fuzzy_text_match(req_cap, all_text):
                        issues.append({
                            "type": "missing_capability",
                            "severity": "medium",
                            "specialty": spec,
                            "requirement": req_cap,
                            "message": f"Claims '{spec}' but no mention of required '{req_cap}'",
                        })

        # Calculate confidence score using diminishing penalty model
        # Each issue reduces confidence, but with diminishing impact
        total_claims = len(specialties) + len(procedures) + len(equipment) + len(capabilities)
        data_completeness = min(1.0, total_claims / 10.0) if total_claims > 0 else 0.1

        if not issues:
            # No issues found
            confidence = 0.7 + (0.3 * data_completeness)
        else:
            high_issues = len([i for i in issues if i["severity"] == "high"])
            med_issues = len([i for i in issues if i["severity"] == "medium"])
            # Diminishing penalty: 1st high = -15%, 2nd = -10%, 3rd+ = -5% each
            penalty = 0.0
            for h in range(high_issues):
                penalty += 0.15 if h == 0 else (0.10 if h == 1 else 0.05)
            for m in range(med_issues):
                penalty += 0.08 if m == 0 else 0.04
            confidence = max(0.10, min(0.95, 1.0 - penalty))

        return {
            "facility": name,
            "valid": len(issues) == 0,
            "confidence": round(confidence, 2),
            "issues": issues,
            "num_issues": len(issues),
            "specialties_checked": specialties,
            "data_completeness": round(data_completeness, 2),
            "latitude": facility_row.get("latitude"),
            "longitude": facility_row.get("longitude"),
            "address_city": facility_row.get("address_city"),
            "address_stateOrRegion": facility_row.get("address_stateOrRegion"),
            "citation": {
                "source": name,
                "specialties": specialties,
                "equipment_found": equipment[:5],
                "procedures_found": procedures[:5],
                "capacity": capacity if capacity and not pd.isna(capacity) else None,
            },
        }

    def _specialty_matches_procedure(self, specialty: str, procedure_key: str) -> bool:
        """Check if a specialty maps to a procedure requirement key."""
        mapping = {
            "neurosurgery": ["neurosurgery"],
            "cardiac_surgery": ["cardiology", "cardiacSurgery", "cardiothoracicSurgery"],
            "cataract_surgery": ["ophthalmology", "corneaOphthalmology"],
            "dialysis": ["nephrology"],
            "orthopedic_surgery": ["orthopedicSurgery"],
            "oncology": ["oncology", "hematologyAndOncology", "radiationOncology"],
        }
        return specialty in mapping.get(procedure_key, [])

    @staticmethod
    def _fuzzy_text_match(needle: str, haystack: str, threshold: int = 75) -> bool:
        """
        Check if `needle` is mentioned in `haystack` using fuzzy matching.
        Uses rapidfuzz token_set_ratio (handles reordering, partial matches,
        abbreviations like "CT" vs "CT scanner").
        Falls back to simple substring matching if rapidfuzz is unavailable.
        """
        needle_lower = needle.lower()
        haystack_lower = haystack.lower()

        # Fast exact check first
        if needle_lower in haystack_lower:
            return True

        if not _RAPIDFUZZ_AVAILABLE:
            return False

        # Slide a window roughly the size of the needle over the haystack
        # and check fuzzy similarity against each window
        needle_words = needle_lower.split()
        hay_words = haystack_lower.split()
        window_size = max(len(needle_words), 3)

        for i in range(max(1, len(hay_words) - window_size + 1)):
            window = " ".join(hay_words[i : i + window_size])
            score = _fuzz.token_set_ratio(needle_lower, window)
            if score >= threshold:
                return True

        return False

    def validate_all_facilities(self) -> Dict:
        """Run constraint validation on all facilities."""
        results = []
        for _, row in self.flat_df.iterrows():
            result = self.validate_facility(row)
            if result["issues"]:
                results.append(result)

        results.sort(key=lambda x: x["confidence"])

        # Build step-level citations
        citations = []
        for r in results[:20]:
            citations.append({
                "source": r["facility"],
                "step": "constraint_validation",
                "evidence": r.get("citation", {}),
                "issues_found": len(r["issues"]),
                "confidence": r["confidence"],
            })

        return {
            "agent": "medical_reasoning",
            "action": "constraint_validation",
            "total_checked": len(self.flat_df),
            "facilities_with_issues": len(results),
            "flagged_facilities": results[:20],
            "summary": {
                "high_severity": sum(len([i for i in r["issues"] if i["severity"] == "high"]) for r in results),
                "medium_severity": sum(len([i for i in r["issues"] if i["severity"] == "medium"]) for r in results),
                "avg_confidence": round(sum(r["confidence"] for r in results) / len(results), 2) if results else 1.0,
            },
            "citations": citations,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  2. ANOMALY DETECTION (Isolation Forest)
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_anomalies(self) -> Dict:
        """
        Two-stage anomaly detection:
          Stage 1 — Isolation Forest (contamination='auto', median-imputed)
          Stage 2 — Mahalanobis distance validation (removes false positives)
        """
        feature_cols = ["num_specialties", "num_procedures", "num_equipment", "num_capabilities"]
        df = self.flat_df.copy()

        # ── Median imputation instead of fillna(0) — avoids zero-bias ──
        df["capacity_f"] = df["capacity"].fillna(df["capacity"].median())
        df["doctors_f"] = df["numberDoctors"].fillna(df["numberDoctors"].median())
        feature_cols_full = feature_cols + ["capacity_f", "doctors_f"]

        X = df[feature_cols_full].values

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # ── Stage 1: Isolation Forest with data-driven threshold ──
        iso_forest = IsolationForest(
            n_estimators=200,
            contamination="auto",       # data-driven instead of fixed 5%
            random_state=42,
        )
        predictions = iso_forest.fit_predict(X_scaled)
        iso_scores = iso_forest.decision_function(X_scaled)

        # ── Stage 2: Mahalanobis distance validation ──
        # Only keep IF outliers that are also Mahalanobis outliers (chi² p < 0.01)
        cov = np.cov(X_scaled, rowvar=False)
        try:
            cov_inv = np.linalg.inv(cov + 1e-6 * np.eye(cov.shape[0]))
        except np.linalg.LinAlgError:
            cov_inv = np.linalg.pinv(cov)

        mean_vec = X_scaled.mean(axis=0)
        maha_dists = np.array([
            mahalanobis(x, mean_vec, cov_inv) for x in X_scaled
        ])

        # Chi-squared critical value for p=0.01 with len(feature_cols_full) dof
        from scipy.stats import chi2
        chi2_threshold = chi2.ppf(0.99, df=len(feature_cols_full))
        maha_outlier = maha_dists**2 > chi2_threshold

        # Combined: must be flagged by BOTH stages
        combined_outlier = (predictions == -1) & maha_outlier
        df["anomaly_label"] = np.where(combined_outlier, -1, 1)
        df["anomaly_score"] = iso_scores
        df["mahalanobis_dist"] = maha_dists

        anomalies = df[df["anomaly_label"] == -1].sort_values("anomaly_score")

        results = []
        for _, row in anomalies.iterrows():
            reasons = []
            if row["num_procedures"] > 10 and row["num_equipment"] < 2:
                reasons.append("High procedure count but minimal equipment")
            if row["capacity_f"] > 0 and row["doctors_f"] > 0 and row["capacity_f"] / row["doctors_f"] > 50:
                reasons.append(f"Extreme bed-to-doctor ratio: {row['capacity_f'] / row['doctors_f']:.0f}")
            if row["num_specialties"] > 8:
                reasons.append(f"Unusually high specialty count: {row['num_specialties']}")
            if row["num_procedures"] > 15 and row["capacity_f"] < 20:
                reasons.append("Many procedures claimed but very low capacity")
            if not reasons:
                reasons.append("Statistical outlier confirmed by both Isolation Forest and Mahalanobis distance")

            results.append({
                "facility": row["name"],
                "city": row["address_city"],
                "region": row.get("address_stateOrRegion"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "anomaly_score": round(float(row["anomaly_score"]), 3),
                "mahalanobis_distance": round(float(row["mahalanobis_dist"]), 2),
                "num_specialties": int(row["num_specialties"]),
                "num_procedures": int(row["num_procedures"]),
                "num_equipment": int(row["num_equipment"]),
                "capacity": row["capacity_f"],
                "doctors": row["doctors_f"],
                "reasons": reasons,
            })

        citations = [
            {
                "source": r["facility"],
                "step": "two_stage_anomaly_detection",
                "iso_score": r["anomaly_score"],
                "mahalanobis": r["mahalanobis_distance"],
                "features": {
                    "specialties": r["num_specialties"],
                    "procedures": r["num_procedures"],
                    "equipment": r["num_equipment"],
                    "capacity": r["capacity"],
                    "doctors": r["doctors"],
                },
                "reasons": r["reasons"],
            }
            for r in results[:20]
        ]

        return {
            "agent": "medical_reasoning",
            "action": "anomaly_detection",
            "model": "IsolationForest + Mahalanobis (two-stage)",
            "total_checked": len(df),
            "stage1_outliers": int((predictions == -1).sum()),
            "stage2_confirmed": len(results),
            "anomalies_found": len(results),
            "results": results[:20],
            "citations": citations,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  3. RED FLAG PATTERN ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_red_flags(self) -> Dict:
        """Scan free-text for language patterns indicating temporary/dubious services."""
        flagged = []

        for _, row in self.flat_df.iterrows():
            doc = row.get("document_text", "")
            procs = " ".join(row.get("procedure", []))
            caps = " ".join(row.get("capability", []))
            full_text = f"{doc} {procs} {caps}".lower()

            flags = []
            for category, patterns in RED_FLAG_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, full_text):
                        match = re.search(pattern, full_text)
                        flags.append({
                            "category": category,
                            "pattern": pattern,
                            "matched_text": match.group(0) if match else "",
                        })

            if flags:
                flagged.append({
                    "facility": row["name"],
                    "city": row.get("address_city"),
                    "region": row.get("address_stateOrRegion"),
                    "latitude": row.get("latitude"),
                    "longitude": row.get("longitude"),
                    "flags": flags,
                    "num_flags": len(flags),
                    "recommendation": self._generate_recommendation(flags),
                })

        flagged.sort(key=lambda x: x["num_flags"], reverse=True)

        return {
            "agent": "medical_reasoning",
            "action": "red_flag_detection",
            "total_scanned": len(self.flat_df),
            "facilities_flagged": len(flagged),
            "results": flagged[:20],
        }

    def _generate_recommendation(self, flags: List[Dict]) -> str:
        categories = set(f["category"] for f in flags)
        if "visiting_specialist" in categories:
            return "Likely relies on visiting specialists — verify permanent staffing"
        if "temporary_service" in categories:
            return "Appears to offer temporary/camp-based services — not permanent capability"
        if "vague_claim" in categories:
            return "Contains vague capability claims — verify specific procedures"
        return "Review flagged language patterns"

    # ═══════════════════════════════════════════════════════════════════════════
    #  4. MEDICAL DESERT ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def identify_coverage_gaps(self, specialty: Optional[str] = None) -> Dict:
        """Identify regions with no or very few facilities for a given specialty."""
        df = self.flat_df.copy()

        if specialty:
            df_spec = df[df["specialties"].apply(lambda s: specialty in s)]
        else:
            df_spec = df

        region_counts = df_spec["address_stateOrRegion"].fillna("Unknown").value_counts()
        all_regions = df["address_stateOrRegion"].fillna("Unknown").unique()

        # Find regions with 0 or very few facilities for this specialty
        gaps = []
        for region in all_regions:
            count = region_counts.get(region, 0)
            total_in_region = len(df[df["address_stateOrRegion"].fillna("Unknown") == region])
            if count <= 1:
                # Get approximate coordinates for this region
                lat, lng = geocode_facility("", region)
                gap_entry = {
                    "region": region,
                    "specialty_count": int(count),
                    "total_facilities": total_in_region,
                    "gap_severity": "critical" if count == 0 else "high",
                }
                if lat is not None and lng is not None:
                    gap_entry["latitude"] = lat
                    gap_entry["longitude"] = lng
                gaps.append(gap_entry)

        gaps.sort(key=lambda x: x["specialty_count"])

        return {
            "agent": "medical_reasoning",
            "action": "coverage_gap_analysis",
            "specialty": specialty or "all",
            "regions_analyzed": len(all_regions),
            "gaps_found": len(gaps),
            "gaps": gaps,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  5. SINGLE POINT OF FAILURE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def single_point_of_failure_analysis(self) -> Dict:
        """Deep analysis of procedures/specialties with dangerous concentration."""
        spec_counter = Counter()
        spec_facilities = {}
        for _, row in self.flat_df.iterrows():
            for s in row["specialties"]:
                spec_counter[s] += 1
                spec_facilities.setdefault(s, []).append({
                    "name": row["name"],
                    "city": row.get("address_city"),
                    "region": row.get("address_stateOrRegion"),
                })

        critical = []
        for spec, count in spec_counter.items():
            if count <= 3:
                facilities = spec_facilities[spec]
                regions = set(f.get("region") for f in facilities if f.get("region"))
                critical.append({
                    "specialty": spec,
                    "facility_count": count,
                    "facilities": facilities,
                    "regions_covered": list(regions),
                    "risk_level": "critical" if count == 1 else "high" if count == 2 else "medium",
                })

        critical.sort(key=lambda x: x["facility_count"])

        return {
            "agent": "medical_reasoning",
            "action": "single_point_of_failure",
            "total_specialties": len(spec_counter),
            "critical_specialties": len(critical),
            "results": critical,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  MAIN DISPATCHER
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Route a medical reasoning query to the appropriate handler."""
        t0 = time.time()
        ql = query.lower()

        if re.search(r"valid|claim.*lack|claim.*but|really.*offer", ql):
            result = self.validate_all_facilities()
        elif re.search(r"anomal|unusual|suspicious|outlier|isolation", ql):
            result = self.detect_anomalies()
        elif re.search(r"red flag|temporary|visiting|camp|mission", ql):
            result = self.detect_red_flags()
        elif re.search(r"desert|gap|coverage|underserved|cold spot", ql):
            from backend.core.config import MEDICAL_SPECIALTIES_MAP
            specialty = None
            for sid, kws in MEDICAL_SPECIALTIES_MAP.items():
                for kw in kws:
                    if kw in ql:
                        specialty = sid
                        break
                if specialty:
                    break
            result = self.identify_coverage_gaps(specialty)
        elif re.search(r"single point|few facilit|depend|rare", ql):
            result = self.single_point_of_failure_analysis()
        else:
            # Run all analyses and combine
            validation = self.validate_all_facilities()
            anomalies = self.detect_anomalies()
            result = {
                "agent": "medical_reasoning",
                "action": "comprehensive_analysis",
                "validation": validation,
                "anomalies": anomalies,
            }

        result["query"] = query
        result["duration_ms"] = round((time.time() - t0) * 1000, 2)
        return result
