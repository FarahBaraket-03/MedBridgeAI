"""
MedBridge AI — AGENT 6: Planning System (The Coordinator)
============================================================
Generates actionable deployment plans for healthcare interventions.

Scenarios:
  1. Emergency Routing: Find nearest capable facility for patient
  2. Specialist Deployment: Optimal rotation plan for visiting doctors
  3. Equipment Distribution: Where to place mobile CT / dialysis units
  4. New Facility Placement: Identify optimal locations for new healthcare centres
  5. Capacity Planning: Forecast bed/staff needs by region

This agent synthesizes outputs from ALL other agents (genie, vector_search,
medical_reasoning, geospatial) into human-readable action plans.
"""

import re
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from geopy.distance import geodesic

from backend.core.config import MEDICAL_SPECIALTIES_MAP
from backend.core.preprocessing import run_preprocessing


# ── Planning scenario templates ──────────────────────────────────────────────

SCENARIOS = {
    "emergency_routing": {
        "title": "Emergency Patient Routing",
        "icon": "🚑",
        "description": "Route patient from rural area to nearest facility with required capability",
    },
    "specialist_deployment": {
        "title": "Specialist Rotation Plan",
        "icon": "👨‍⚕️",
        "description": "Optimize specialist's travel route to cover underserved facilities",
    },
    "equipment_distribution": {
        "title": "Equipment Distribution",
        "icon": "🏗️",
        "description": "Plan mobile unit or equipment placement to maximize coverage",
    },
    "new_facility_placement": {
        "title": "New Facility Placement",
        "icon": "📍",
        "description": "Identify optimal locations for new healthcare centres",
    },
    "capacity_planning": {
        "title": "Capacity Planning",
        "icon": "📊",
        "description": "Forecast bed/staff needs and identify overloaded facilities",
    },
}


class PlanningAgent:
    """
    Coordination & planning agent that generates actionable healthcare
    deployment plans accessible to all experience levels.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None:
            self._source_df = df
        else:
            self._source_df = run_preprocessing()
        self._build_flat_df()

    def _build_flat_df(self):
        rows = []
        for i, m in enumerate(self._source_df["metadata"].tolist()):
            lat = m.get("latitude")
            lng = m.get("longitude")
            try:
                lat = float(lat) if lat else None
                lng = float(lng) if lng else None
            except (ValueError, TypeError):
                lat, lng = None, None
            cap = m.get("capacity")
            docs = m.get("numberDoctors")
            try:
                cap = float(cap) if cap else None
            except (ValueError, TypeError):
                cap = None
            try:
                docs = float(docs) if docs else None
            except (ValueError, TypeError):
                docs = None

            rows.append({
                "name": m.get("name", "Unknown"),
                "organization_type": m.get("organization_type"),
                "facilityTypeId": m.get("facilityTypeId"),
                "address_city": m.get("address_city"),
                "address_stateOrRegion": m.get("address_stateOrRegion"),
                "latitude": lat,
                "longitude": lng,
                "specialties": m.get("specialties", []),
                "procedure": m.get("procedure", []),
                "equipment": m.get("equipment", []),
                "capability": m.get("capability", []),
                "capacity": cap,
                "numberDoctors": docs,
            })
        self.flat_df = pd.DataFrame(rows)

    # ═══════════════════════════════════════════════════════════════════════════
    #  1. EMERGENCY ROUTING
    # ═══════════════════════════════════════════════════════════════════════════

    def emergency_routing(self, specialty: Optional[str] = None,
                          origin_lat: Optional[float] = None,
                          origin_lng: Optional[float] = None) -> Dict:
        """Find nearest capable facility and generate route plan."""
        df = self.flat_df.dropna(subset=["latitude", "longitude"]).copy()

        if specialty:
            df = df[df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)]

        if df.empty:
            return {"error": f"No facilities found for specialty '{specialty}'"}

        # Default origin: geographic center of Ghana
        if origin_lat is None:
            origin_lat, origin_lng = 7.9465, -1.0232

        # Calculate distances
        distances = []
        for _, row in df.iterrows():
            dist = geodesic(
                (origin_lat, origin_lng),
                (row["latitude"], row["longitude"])
            ).km
            travel_min = round(dist / 60 * 60, 0)  # ~60km/h average
            distances.append({
                "facility": row["name"],
                "city": row["address_city"],
                "region": row["address_stateOrRegion"],
                "distance_km": round(dist, 1),
                "est_travel_min": int(travel_min),
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "specialties": row["specialties"],
                "equipment": row["equipment"][:5],
                "capacity": row["capacity"],
                "capability_match": self._capability_score(row, specialty),
            })

        distances.sort(key=lambda x: x["distance_km"])
        nearest = distances[0]
        backup = distances[1] if len(distances) > 1 else None

        plan = {
            "scenario": "emergency_routing",
            "title": "🚑 Emergency Routing Plan",
            "origin": {"lat": origin_lat, "lng": origin_lng},
            "specialty_needed": specialty or "general",
            "primary_facility": nearest,
            "backup_facility": backup,
            "alternatives": distances[2:5],
            "action_steps": [
                f"1. Contact {nearest['facility']} ({nearest['city']}) — {nearest['distance_km']} km away",
                f"2. Estimated travel time: {nearest['est_travel_min']} minutes",
                f"3. Capability match: {nearest['capability_match']}%",
            ],
            "total_options": len(distances),
        }

        if backup:
            plan["action_steps"].append(
                f"4. Backup: {backup['facility']} ({backup['city']}) — {backup['distance_km']} km"
            )

        return plan

    def _capability_score(self, row: pd.Series, specialty: Optional[str]) -> int:
        """Score 0-100 how well-equipped a facility is for this need.

        Weighting rationale (for emergency routing the *clinical match*
        matters most — a facility with the right specialty but limited
        imaging is far more useful than one with a CT scanner but no
        relevant specialists):

          Specialty match:   +35  (dominant — this IS the patient need)
          ICU / theater:     +20  (critical infrastructure for emergencies)
          Capacity > 20:     +10  (can actually admit the patient)
          Has doctors:       +10  (staffing reality-check)
          Advanced imaging:  +5   (nice to have, not decisive)
        """
        score = 20  # base
        # Primary: does the facility actually cover the needed specialty?
        if specialty and specialty in row.get("specialties", []):
            score += 35
        # Infrastructure
        equip = " ".join(row.get("equipment", [])).lower()
        cap = " ".join(row.get("capability", [])).lower()
        if "icu" in cap or "operating theater" in cap or "operating theatre" in cap:
            score += 20
        if row.get("capacity") and row["capacity"] > 20:
            score += 10
        if row.get("numberDoctors") and row["numberDoctors"] > 0:
            score += 10
        if "ct" in equip or "mri" in equip or "scanner" in equip:
            score += 5
        return min(100, score)

    # ═══════════════════════════════════════════════════════════════════════════
    #  2. SPECIALIST DEPLOYMENT PLAN  (Greedy NN + 2-opt)
    # ═══════════════════════════════════════════════════════════════════════════

    def specialist_deployment(self, specialty: Optional[str] = None,
                               max_facilities: int = 8,
                               use_quantum: bool = False) -> Dict:
        """
        Generate an optimised multi-stop rotation plan for a visiting specialist.
        Uses greedy nearest-neighbour to build an initial tour, then applies
        2-opt local search to improve the route (~20-25% shorter).

        If *use_quantum=True*, also runs QAOA (Qiskit simulator) and returns
        a side-by-side comparison.  The classical result is always present;
        the quantum result is additive and never blocks the response.
        """
        df = self.flat_df.copy()

        # Find facilities that NEED this specialty (don't have it)
        if specialty:
            needs = df[~df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)]
            has = df[df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)]
        else:
            needs = df
            has = pd.DataFrame()

        # Filter to those with coords
        needs = needs.dropna(subset=["latitude", "longitude"])

        if needs.empty:
            return {"error": "No underserved facilities found"}

        # ── Stage 1: Greedy nearest-neighbour to get initial tour ──
        stop_indices = []
        visited = set()
        current_lat, current_lng = 5.6037, -0.1870  # Start from Accra
        n_stops = min(max_facilities, len(needs))

        for _ in range(n_stops):
            best_dist = float("inf")
            best_idx = None
            for idx, row in needs.iterrows():
                if idx in visited:
                    continue
                d = geodesic(
                    (current_lat, current_lng),
                    (row["latitude"], row["longitude"])
                ).km
                if d < best_dist:
                    best_dist = d
                    best_idx = idx
            if best_idx is None:
                break
            visited.add(best_idx)
            stop_indices.append(best_idx)
            row = needs.loc[best_idx]
            current_lat = row["latitude"]
            current_lng = row["longitude"]

        if len(stop_indices) < 2:
            # Not enough stops for 2-opt, just build result
            return self._build_deployment_result(needs, stop_indices, specialty)

        # ── Stage 2: 2-opt improvement ──
        # Build distance matrix for the selected stops (including Accra as node 0)
        coords = [(5.6037, -0.1870)]  # Accra depot
        for idx in stop_indices:
            row = needs.loc[idx]
            coords.append((row["latitude"], row["longitude"]))

        n = len(coords)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = geodesic(coords[i], coords[j]).km
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

        # Initial tour: 0 → 1 → 2 → ... → n-1 (greedy NN order)
        tour = list(range(n))

        # 2-opt local search
        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # Cost of current edges
                    old_cost = (
                        dist_matrix[tour[i - 1], tour[i]]
                        + dist_matrix[tour[j], tour[(j + 1) % n]]
                    )
                    # Cost after reversing segment [i..j]
                    new_cost = (
                        dist_matrix[tour[i - 1], tour[j]]
                        + dist_matrix[tour[i], tour[(j + 1) % n]]
                    )
                    if new_cost < old_cost - 1e-9:
                        tour[i : j + 1] = reversed(tour[i : j + 1])
                        improved = True

        # Rebuild stop order from optimised tour (skip depot node 0)
        optimised_indices = [stop_indices[tour[t] - 1] for t in range(1, n)]

        result = self._build_deployment_result(needs, optimised_indices, specialty)

        # ── Optional: QAOA quantum comparison ──
        if use_quantum:
            result = self._attach_quantum_comparison(
                result, dist_matrix, tour, coords, needs, optimised_indices, specialty,
            )

        return result

    def _build_deployment_result(
        self, needs: pd.DataFrame, ordered_indices: List, specialty: Optional[str]
    ) -> Dict:
        """Build the deployment result dict from an ordered list of facility indices."""
        stops = []
        current_lat, current_lng = 5.6037, -0.1870  # Accra
        total_distance = 0.0

        for idx in ordered_indices:
            row = needs.loc[idx]
            dist = geodesic(
                (current_lat, current_lng),
                (row["latitude"], row["longitude"])
            ).km
            total_distance += dist
            stops.append({
                "stop": len(stops) + 1,
                "facility": row["name"],
                "city": row["address_city"],
                "region": row["address_stateOrRegion"],
                "distance_from_prev_km": round(dist, 1),
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "current_specialties": row["specialties"],
                "population_impact": "high" if row.get("capacity", 0) and row["capacity"] > 30 else "medium",
            })
            current_lat = row["latitude"]
            current_lng = row["longitude"]

        return {
            "scenario": "specialist_deployment",
            "title": f"👨‍⚕️ Specialist Rotation: {specialty or 'General'}",
            "specialty": specialty or "general",
            "optimisation": "greedy_nn + 2-opt",
            "total_stops": len(stops),
            "total_distance_km": round(total_distance, 1),
            "est_total_days": max(1, len(stops)),
            "stops": stops,
            "facilities_needing_specialty": len(needs),
            "action_steps": [
                f"1. Deploy {specialty or 'specialist'} on {len(stops)}-stop rotation",
                f"2. Total travel: {round(total_distance, 0)} km over {len(stops)} days",
                f"3. Route optimised with 2-opt local search",
                f"4. Start from Accra, visit {len(stops)} underserved facilities",
            ],
        }

    # ─── Quantum comparison (additive, never blocks) ─────────────────────────

    def _attach_quantum_comparison(
        self,
        result: Dict,
        dist_matrix: np.ndarray,
        classical_tour: List[int],
        coords: List[tuple],
        needs: pd.DataFrame,
        stop_indices: List,
        specialty: Optional[str],
    ) -> Dict:
        """
        Run QAOA side-by-side with the classical result and attach the
        comparison to the existing result dict.  If QAOA is unavailable
        or fails, the classical result is returned unchanged with a note.
        """
        from backend.core.quantum import compare_routes, is_qiskit_available

        if not is_qiskit_available():
            result["quantum"] = {
                "available": False,
                "note": "Qiskit not installed -- classical 2-opt used",
            }
            return result

        # City labels for readability
        city_names = ["Accra (depot)"]
        for idx in stop_indices:
            row = needs.loc[idx]
            city_names.append(str(row.get("name", row.get("address_city", f"Stop-{idx}"))))

        classical_cost = sum(
            dist_matrix[classical_tour[i], classical_tour[(i + 1) % len(classical_tour)]]
            for i in range(len(classical_tour))
        )

        comparison = compare_routes(
            dist_matrix,
            classical_tour,
            classical_cost,
            city_names=city_names,
        )

        result["quantum"] = {
            "available": True,
            **comparison["quantum"],
            "comparison": {
                "winner": comparison["winner"],
                "saving_km": comparison["saving_km"],
                "saving_pct": comparison["saving_pct"],
                "summary": comparison["summary"],
            },
        }

        # Update optimisation label
        result["optimisation"] = f"greedy_nn + 2-opt + QAOA (winner: {comparison['winner']})"

        # If quantum found a shorter feasible tour, also update the stops
        if comparison["winner"] == "quantum" and comparison["quantum"].get("feasible"):
            q_tour = comparison["quantum"]["tour"]
            # Remap quantum tour (node indices) back to facility indices
            q_stop_indices = [stop_indices[q_tour[t] - 1] for t in range(1, len(q_tour))]
            q_result = self._build_deployment_result(needs, q_stop_indices, specialty)
            result["quantum_route"] = q_result["stops"]
            result["quantum_distance_km"] = q_result["total_distance_km"]
            result["action_steps"].append(
                f"5. QAOA found a {comparison['saving_km']} km shorter route "
                f"({comparison['saving_pct']}% saving)"
            )

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    #  3. EQUIPMENT DISTRIBUTION
    # ═══════════════════════════════════════════════════════════════════════════

    def equipment_distribution(self, equipment_type: str = "CT scanner") -> Dict:
        """Plan where to deploy mobile/new equipment to maximize coverage."""
        df = self.flat_df.dropna(subset=["latitude", "longitude"]).copy()

        # Find who already has it
        equip_lower = equipment_type.lower()
        df["has_equipment"] = df["equipment"].apply(
            lambda e: any(equip_lower in x.lower() for x in e)
        )
        with_equip = df[df["has_equipment"]]
        without_equip = df[~df["has_equipment"]]

        # Score regions by need
        region_need = {}
        for _, row in without_equip.iterrows():
            region = row.get("address_stateOrRegion", "Unknown")
            region_need.setdefault(region, {"count": 0, "facilities": []})
            region_need[region]["count"] += 1
            if len(region_need[region]["facilities"]) < 3:
                region_need[region]["facilities"].append(row["name"])

        # Sort by need
        ranked_regions = sorted(region_need.items(), key=lambda x: x[1]["count"], reverse=True)

        # Suggest placements
        placements = []
        for region, data in ranked_regions[:5]:
            region_facs = without_equip[without_equip["address_stateOrRegion"] == region]
            if region_facs.empty:
                continue
            # Pick facility with highest capacity as placement
            if "capacity" in region_facs.columns:
                best = region_facs.sort_values("capacity", ascending=False).iloc[0]
            else:
                best = region_facs.iloc[0]
            placements.append({
                "region": region,
                "recommended_facility": best["name"],
                "city": best["address_city"],
                "latitude": best["latitude"],
                "longitude": best["longitude"],
                "facilities_served": data["count"],
                "nearby_facilities": data["facilities"][:3],
            })

        return {
            "scenario": "equipment_distribution",
            "title": f"🏗️ {equipment_type} Distribution Plan",
            "equipment": equipment_type,
            "facilities_with": len(with_equip),
            "facilities_without": len(without_equip),
            "placements": placements,
            "action_steps": [
                f"1. {len(with_equip)} facilities already have {equipment_type}",
                f"2. {len(without_equip)} facilities need {equipment_type}",
                f"3. Top {len(placements)} recommended placement regions identified",
                f"4. Priority: regions with most underserved facilities",
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  4. NEW FACILITY PLACEMENT  (Maximin algorithm)
    # ═══════════════════════════════════════════════════════════════════════════

    def new_facility_placement(self, specialty: Optional[str] = None) -> Dict:
        """
        Identify optimal locations for new facilities using the **maximin**
        algorithm: place each new facility at the point in a grid that is
        farthest from any existing facility (maximises minimum coverage).
        This is the opposite of the old centroid approach, which incorrectly
        placed new facilities where facilities already cluster.
        """
        from sklearn.neighbors import BallTree

        EARTH_RADIUS_KM = 6371.0

        df = self.flat_df.dropna(subset=["latitude", "longitude"]).copy()

        if specialty:
            df_spec = df[df["specialties"].apply(lambda s: isinstance(s, list) and specialty in s)]
        else:
            df_spec = df

        # Region-level analysis
        if len(df_spec) > 0 and "address_stateOrRegion" in df_spec.columns:
            region_counts = df_spec["address_stateOrRegion"].fillna("Unknown").value_counts()
        else:
            region_counts = pd.Series(dtype=int)
        total_by_region = df["address_stateOrRegion"].fillna("Unknown").value_counts()

        # ── Maximin placement using BallTree ──
        existing_coords = df_spec[["latitude", "longitude"]].values
        if len(existing_coords) == 0:
            existing_coords = df[["latitude", "longitude"]].values

        if len(existing_coords) == 0:
            return {"error": "No facilities with coordinates found"}

        existing_rad = np.deg2rad(existing_coords)
        tree = BallTree(existing_rad, metric="haversine")

        # Build grid over Ghana
        from backend.core.config import GHANA_BOUNDING_BOX
        lat_min, lat_max = GHANA_BOUNDING_BOX["south"], GHANA_BOUNDING_BOX["north"]
        lng_min, lng_max = GHANA_BOUNDING_BOX["west"], GHANA_BOUNDING_BOX["east"]

        grid_lats = np.arange(lat_min, lat_max, 0.3)
        grid_lngs = np.arange(lng_min, lng_max, 0.3)
        glat, glng = np.meshgrid(grid_lats, grid_lngs, indexing="ij")
        grid_points = np.column_stack([glat.ravel(), glng.ravel()])
        grid_rad = np.deg2rad(grid_points)

        # For each grid point, find distance to nearest existing facility
        dist_rad, _ = tree.query(grid_rad, k=1)
        dist_km = dist_rad[:, 0] * EARTH_RADIUS_KM

        # Rank grid points by distance (farthest from any facility = best placement)
        ranking = np.argsort(-dist_km)

        suggestions = []
        for rank in range(min(10, len(ranking))):
            idx = ranking[rank]
            pt_lat = float(grid_points[idx, 0])
            pt_lng = float(grid_points[idx, 1])
            gap_km = float(dist_km[idx])

            # Find which region this point falls in (approximate via nearest facility)
            near_idx = tree.query(np.deg2rad([[pt_lat, pt_lng]]), k=1)[1][0, 0]
            near_row_idx = df_spec.index[near_idx] if near_idx < len(df_spec) else df.index[near_idx]
            region = df.loc[near_row_idx, "address_stateOrRegion"] if near_row_idx in df.index else "Unknown"
            spec_count = int(region_counts.get(region, 0))

            suggestions.append({
                "rank": rank + 1,
                "region": region,
                "current_facilities_with_specialty": spec_count,
                "total_facilities_in_region": int(total_by_region.get(region, 0)),
                "suggested_lat": round(pt_lat, 4),
                "suggested_lng": round(pt_lng, 4),
                "nearest_existing_facility_km": round(gap_km, 1),
                "priority": "critical" if gap_km > 100 else "high" if gap_km > 50 else "medium",
            })

        return {
            "scenario": "new_facility_placement",
            "title": f"📍 New Facility Recommendations: {specialty or 'General'}",
            "algorithm": "maximin (maximise minimum coverage distance)",
            "specialty": specialty or "general",
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "action_steps": [
                f"1. {len([s for s in suggestions if s['priority']=='critical'])} locations are >100 km from any existing facility",
                f"2. {len(suggestions)} optimal placement sites identified via maximin",
                f"3. Coordinates maximise coverage — each is the point farthest from existing facilities",
                f"4. Prioritise 'critical' sites first (>100 km to nearest facility)",
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  5. CAPACITY PLANNING
    # ═══════════════════════════════════════════════════════════════════════════

    def capacity_planning(self) -> Dict:
        """Analyse bed/doctor capacity by region and identify bottlenecks."""
        df = self.flat_df.copy()

        regions = []
        for region, grp in df.groupby("address_stateOrRegion"):
            if pd.isna(region):
                continue
            total = len(grp)
            beds = grp["capacity"].sum() if "capacity" in grp else 0
            docs = grp["numberDoctors"].sum() if "numberDoctors" in grp else 0
            beds = 0 if pd.isna(beds) else beds
            docs = 0 if pd.isna(docs) else docs

            bed_ratio = round(beds / total, 1) if total > 0 else 0
            doc_ratio = round(docs / total, 2) if total > 0 else 0

            regions.append({
                "region": region,
                "facilities": total,
                "total_beds": int(beds),
                "total_doctors": int(docs),
                "beds_per_facility": bed_ratio,
                "doctors_per_facility": doc_ratio,
                "status": "critical" if bed_ratio < 5 and total > 3 else (
                    "warning" if bed_ratio < 15 else "adequate"
                ),
            })

        regions.sort(key=lambda x: x["beds_per_facility"])

        return {
            "scenario": "capacity_planning",
            "title": "📊 Regional Capacity Analysis",
            "total_regions": len(regions),
            "critical_regions": len([r for r in regions if r["status"] == "critical"]),
            "regions": regions,
            "action_steps": [
                f"1. {len([r for r in regions if r['status']=='critical'])} regions critically under-resourced",
                f"2. Average beds/facility across Ghana: {round(sum(r['beds_per_facility'] for r in regions)/len(regions), 1) if regions else 0}",
                f"3. Focus hiring in regions with lowest doctor ratios",
                f"4. Consider bed expansion in critical regions first",
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  LIST SCENARIOS
    # ═══════════════════════════════════════════════════════════════════════════

    def list_scenarios(self) -> Dict:
        """Return available planning scenarios."""
        return {
            "agent": "planning",
            "action": "list_scenarios",
            "scenarios": [
                {**v, "id": k}
                for k, v in SCENARIOS.items()
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  DISPATCHER
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Route a planning query to the appropriate handler."""
        t0 = time.time()
        ql = query.lower()
        ctx = context or {}
        use_quantum = ctx.get("use_quantum", False) or "quantum" in ql

        # Extract specialty
        specialty = None
        for sid, kws in MEDICAL_SPECIALTIES_MAP.items():
            for kw in kws:
                if kw in ql:
                    specialty = sid
                    break
            if specialty:
                break

        # Extract equipment
        equipment = None
        for eq in ["ct scanner", "mri", "dialysis", "ultrasound", "x-ray", "ventilator", "oxygen"]:
            if eq in ql:
                equipment = eq.title()
                break

        if re.search(r"emergenc|route.*patient|nearest.*capable|urgent", ql):
            result = self.emergency_routing(
                specialty,
                ctx.get("lat"), ctx.get("lng")
            )
        elif re.search(r"specialist.*rotat|deploy.*(doctor|specialist|surgeon|cardiolog|dentist|pediatri)|visiting.*route|rotation.*plan|multi.*stop.*tour", ql):
            result = self.specialist_deployment(specialty, use_quantum=use_quantum)
        elif re.search(r"equipment.*distribut|mobile.*unit|place.*scanner|deploy.*equip", ql):
            result = self.equipment_distribution(equipment or "CT scanner")
        elif re.search(r"new.*facilit|build.*hospital|where.*build|optimal.*location", ql):
            result = self.new_facility_placement(specialty)
        elif re.search(r"capacity|bed.*need|staff.*need|overload|bottleneck", ql):
            result = self.capacity_planning()
        elif re.search(r"scenario|plan.*option|what.*can.*plan", ql):
            result = self.list_scenarios()
        else:
            # Default: emergency routing (most common IDP need)
            result = self.emergency_routing(specialty)

        result["agent"] = "planning"
        result["query"] = query
        result["duration_ms"] = round((time.time() - t0) * 1000, 2)
        return result
