"""
MedBridge AI — AGENT 5: Geospatial (The Navigator)
=====================================================
Distance calculations, coverage analysis, and medical desert detection.

Uses:
  - geopy: Haversine / geodesic distance
  - scipy.spatial: Voronoi / KDTree for nearest-neighbour
  - NumPy grid-based cold-spot analysis

INPUT:  Location-aware queries (lat/lng, radius, region, specialty)
OUTPUT: Distance results, coverage maps, gap analysis
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from geopy.distance import geodesic

from backend.core.config import (
    GHANA_BOUNDING_BOX,
    GHANA_CENTER_LAT,
    GHANA_CENTER_LNG,
    MEDICAL_SPECIALTIES_MAP,
)
from backend.core.geocoding import GHANA_CITY_COORDS, GHANA_REGION_COORDS
from backend.core.preprocessing import run_preprocessing


class GeospatialAgent:
    """
    Geospatial intelligence agent for medical facility network analysis.
    Handles distance queries, coverage gaps, and medical desert detection.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None:
            self._source_df = df
        else:
            self._source_df = run_preprocessing()
        self._build_geo_df()

    def _build_geo_df(self):
        """Build dataframe with valid lat/lng for geospatial ops."""
        rows = []
        for i, m in enumerate(self._source_df["metadata"].tolist()):
            lat = m.get("latitude")
            lng = m.get("longitude")
            try:
                lat = float(lat) if lat else None
                lng = float(lng) if lng else None
            except (ValueError, TypeError):
                lat, lng = None, None

            rows.append({
                "name": m.get("name", "Unknown"),
                "pk_unique_id": m.get("pk_unique_id"),
                "organization_type": m.get("organization_type"),
                "facilityTypeId": m.get("facilityTypeId"),
                "address_city": m.get("address_city"),
                "address_stateOrRegion": m.get("address_stateOrRegion"),
                "latitude": lat,
                "longitude": lng,
                "specialties": m.get("specialties", []),
                "procedure": m.get("procedure", []),
                "capacity": m.get("capacity"),
                "numberDoctors": m.get("numberDoctors"),
            })
        self.geo_df = pd.DataFrame(rows)
        self.geo_df["capacity"] = pd.to_numeric(self.geo_df["capacity"], errors="coerce")
        self.geo_df["numberDoctors"] = pd.to_numeric(self.geo_df["numberDoctors"], errors="coerce")

        # Subset with valid coordinates
        self.valid_coords = self.geo_df.dropna(subset=["latitude", "longitude"]).copy()

    # ═══════════════════════════════════════════════════════════════════════════
    #  1. DISTANCE QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def facilities_within_radius(
        self,
        lat: float,
        lng: float,
        radius_km: float = 50.0,
        specialty: Optional[str] = None,
    ) -> Dict:
        """Find all facilities within a given radius of a point."""
        df = self.valid_coords.copy()
        if specialty:
            df = df[df["specialties"].apply(lambda s: specialty in s)]

        results = []
        for _, row in df.iterrows():
            dist = geodesic((lat, lng), (row["latitude"], row["longitude"])).km
            if dist <= radius_km:
                results.append({
                    "facility": row["name"],
                    "city": row["address_city"],
                    "region": row["address_stateOrRegion"],
                    "distance_km": round(dist, 2),
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "specialties": row["specialties"],
                    "type": row["facilityTypeId"],
                })

        results.sort(key=lambda x: x["distance_km"])

        return {
            "agent": "geospatial",
            "action": "facilities_within_radius",
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "specialty_filter": specialty,
            "total_found": len(results),
            "facilities": results[:30],
        }

    def nearest_facilities(
        self,
        lat: float,
        lng: float,
        k: int = 5,
        specialty: Optional[str] = None,
    ) -> Dict:
        """Find the k nearest facilities to a given point."""
        df = self.valid_coords.copy()
        if specialty:
            df = df[df["specialties"].apply(lambda s: specialty in s)]

        distances = []
        for _, row in df.iterrows():
            dist = geodesic((lat, lng), (row["latitude"], row["longitude"])).km
            distances.append({
                "facility": row["name"],
                "city": row["address_city"],
                "region": row["address_stateOrRegion"],
                "distance_km": round(dist, 2),
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "specialties": row["specialties"],
                "type": row["facilityTypeId"],
            })

        distances.sort(key=lambda x: x["distance_km"])

        return {
            "agent": "geospatial",
            "action": "nearest_facilities",
            "origin": {"lat": lat, "lng": lng},
            "k": k,
            "specialty_filter": specialty,
            "facilities": distances[:k],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  2. COVERAGE GAP ANALYSIS (Grid-Based)
    # ═══════════════════════════════════════════════════════════════════════════

    def coverage_gap_analysis(
        self,
        specialty: Optional[str] = None,
        grid_resolution: float = 0.5,  # degrees (~55 km)
        max_acceptable_distance_km: float = 50.0,
    ) -> Dict:
        """
        Grid-based coverage analysis over Ghana's bounding box.
        Identifies cells where the nearest facility (with an optional specialty
        filter) exceeds max_acceptable_distance_km.
        """
        df = self.valid_coords.copy()
        if specialty:
            df = df[df["specialties"].apply(lambda s: specialty in s)]

        if len(df) == 0:
            return {
                "agent": "geospatial",
                "action": "coverage_gap_analysis",
                "specialty": specialty,
                "message": f"No facilities found with specialty '{specialty}'",
                "gaps": [],
            }

        lat_min, lat_max = GHANA_BOUNDING_BOX["south"], GHANA_BOUNDING_BOX["north"]
        lng_min, lng_max = GHANA_BOUNDING_BOX["west"], GHANA_BOUNDING_BOX["east"]

        lats = np.arange(lat_min, lat_max, grid_resolution)
        lngs = np.arange(lng_min, lng_max, grid_resolution)

        fac_coords = list(zip(df["latitude"], df["longitude"]))
        fac_names = df["name"].tolist()
        fac_cities = df["address_city"].tolist()

        cold_spots = []
        coverage_stats = {"covered": 0, "uncovered": 0}

        for lat in lats:
            for lng in lngs:
                min_dist = float("inf")
                nearest_fac = None
                nearest_city = None
                for idx, (flat, flng) in enumerate(fac_coords):
                    d = geodesic((lat, lng), (flat, flng)).km
                    if d < min_dist:
                        min_dist = d
                        nearest_fac = fac_names[idx]
                        nearest_city = fac_cities[idx]

                if min_dist > max_acceptable_distance_km:
                    coverage_stats["uncovered"] += 1
                    cold_spots.append({
                        "grid_lat": round(lat, 2),
                        "grid_lng": round(lng, 2),
                        "nearest_facility": nearest_fac,
                        "nearest_city": nearest_city,
                        "distance_km": round(min_dist, 1),
                    })
                else:
                    coverage_stats["covered"] += 1

        cold_spots.sort(key=lambda x: x["distance_km"], reverse=True)
        total_cells = coverage_stats["covered"] + coverage_stats["uncovered"]
        coverage_pct = round(
            coverage_stats["covered"] / total_cells * 100, 1
        ) if total_cells > 0 else 0

        return {
            "agent": "geospatial",
            "action": "coverage_gap_analysis",
            "specialty": specialty or "all",
            "grid_resolution_deg": grid_resolution,
            "max_acceptable_km": max_acceptable_distance_km,
            "total_grid_cells": total_cells,
            "coverage_percentage": coverage_pct,
            "cold_spots_found": len(cold_spots),
            "worst_cold_spots": cold_spots[:15],
            "coverage_stats": coverage_stats,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  3. MEDICAL DESERT IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def identify_medical_deserts(
        self,
        specialty: Optional[str] = None,
        threshold_km: float = 75.0,
    ) -> Dict:
        """
        Identify 'medical deserts' — regions where citizens must travel
        >threshold_km to reach a facility offering a given specialty.
        """
        df = self.valid_coords.copy()
        if specialty:
            df = df[df["specialties"].apply(lambda s: specialty in s)]

        if len(df) == 0:
            return {
                "agent": "geospatial",
                "action": "medical_desert_detection",
                "specialty": specialty,
                "message": f"No facilities found for '{specialty}' — entire country is a desert for this specialty",
                "deserts": [],
            }

        # Check from region centers (approximate)
        region_centers = (
            self.geo_df.dropna(subset=["latitude", "longitude"])
            .groupby("address_stateOrRegion")
            .agg({"latitude": "mean", "longitude": "mean", "name": "count"})
            .rename(columns={"name": "total_facilities"})
        )

        fac_coords = list(zip(df["latitude"], df["longitude"]))
        deserts = []

        for region, rc in region_centers.iterrows():
            if pd.isna(region) or region == "Unknown":
                continue
            min_dist = float("inf")
            for flat, flng in fac_coords:
                d = geodesic((rc["latitude"], rc["longitude"]), (flat, flng)).km
                if d < min_dist:
                    min_dist = d  

            if min_dist > threshold_km:
                deserts.append({
                    "region": region,
                    "center_lat": round(rc["latitude"], 4),
                    "center_lng": round(rc["longitude"], 4),
                    "nearest_distance_km": round(min_dist, 1),
                    "total_facilities_in_region": int(rc["total_facilities"]),
                    "severity": "critical" if min_dist > 150 else "high" if min_dist > 100 else "medium",
                })

        deserts.sort(key=lambda x: x["nearest_distance_km"], reverse=True)

        return {
            "agent": "geospatial",
            "action": "medical_desert_detection",
            "specialty": specialty or "all",
            "threshold_km": threshold_km,
            "regions_analyzed": len(region_centers),
            "deserts_found": len(deserts),
            "deserts": deserts,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  4. REGIONAL EQUITY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def regional_equity_analysis(self) -> Dict:
        """Analyse per-region facility density, doctor/bed ratios, specialty counts."""
        df = self.geo_df.copy()
        regions = []

        for region, grp in df.groupby("address_stateOrRegion"):
            if pd.isna(region) or region == "Unknown":
                continue
            total = len(grp)
            docs = grp["numberDoctors"].sum()
            beds = grp["capacity"].sum()
            all_specs = set()
            for specs in grp["specialties"]:
                all_specs.update(specs)

            regions.append({
                "region": region,
                "total_facilities": total,
                "total_doctors": int(docs) if not pd.isna(docs) else 0,
                "total_beds": int(beds) if not pd.isna(beds) else 0,
                "unique_specialties": len(all_specs),
                "specialties": list(all_specs)[:10],
                "beds_per_facility": round(beds / total, 1) if total > 0 and not pd.isna(beds) else 0,
            })

        regions.sort(key=lambda x: x["total_facilities"], reverse=True)

        return {
            "agent": "geospatial",
            "action": "regional_equity_analysis",
            "total_regions": len(regions),
            "regions": regions,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  5. DISTANCE BETWEEN CITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def _geocode_city_from_query(self, query_lower: str) -> tuple:
        """
        Extract a city name from the query and return its approximate lat/lng.
        Uses static geocoding lookup first, then facility coordinate averages.
        Returns (lat, lng) or (None, None).
        """
        # Known Ghana cities to search for (ordered by specificity)
        known_cities = [
            "Cape Coast", "Accra", "Kumasi", "Tamale", "Takoradi",
            "Sunyani", "Bolgatanga", "Wa", "Koforidua", "Tema", "Ho",
            "Techiman", "Sekondi", "Obuasi", "Tarkwa", "Nkawkaw",
            "Winneba", "Hohoe", "Yendi", "Bawku", "Navrongo",
        ]
        for city in known_cities:
            if city.lower() in query_lower:
                # Try static geocoding lookup first
                city_key = city.lower()
                if city_key in GHANA_CITY_COORDS:
                    return GHANA_CITY_COORDS[city_key]
                # Fallback: average from facility coordinates
                match = self.valid_coords[
                    self.valid_coords["address_city"].str.contains(city, case=False, na=False)
                ]
                if not match.empty:
                    return float(match["latitude"].mean()), float(match["longitude"].mean())
        return None, None

    def distance_between_cities(self, city_a: str, city_b: str) -> Dict:
        """Calculate distance between two cities using facility coordinates."""
        df = self.valid_coords.copy()

        a_match = df[df["address_city"].str.contains(city_a, case=False, na=False)]
        b_match = df[df["address_city"].str.contains(city_b, case=False, na=False)]

        if a_match.empty or b_match.empty:
            return {
                "agent": "geospatial",
                "action": "distance_between_cities",
                "error": f"Could not find coordinates for {'city A' if a_match.empty else 'city B'}",
            }

        # Use mean of facility coords as city center proxy
        lat_a = a_match["latitude"].mean()
        lng_a = a_match["longitude"].mean()
        lat_b = b_match["latitude"].mean()
        lng_b = b_match["longitude"].mean()

        dist = geodesic((lat_a, lng_a), (lat_b, lng_b)).km

        return {
            "agent": "geospatial",
            "action": "distance_between_cities",
            "city_a": city_a,
            "city_b": city_b,
            "distance_km": round(dist, 1),
            "facilities_in_a": len(a_match),
            "facilities_in_b": len(b_match),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  MAIN DISPATCHER
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Route a geospatial query to the appropriate handler."""
        t0 = time.time()
        ql = query.lower()

        # Extract specialty if mentioned
        specialty = None
        for sid, kws in MEDICAL_SPECIALTIES_MAP.items():
            for kw in kws:
                if kw in ql:
                    specialty = sid
                    break
            if specialty:
                break

        # Try to extract coordinates from context
        ctx = context or {}
        lat = ctx.get("lat")
        lng = ctx.get("lng")

        # If no coordinates provided, try to geocode city names from the query
        if lat is None or lng is None:
            lat, lng = self._geocode_city_from_query(ql)

        # Parse radius if mentioned
        radius_match = re.search(r"(\d+)\s*km", ql)
        radius_km = float(radius_match.group(1)) if radius_match else 50.0

        if re.search(r"within|near|radius|around|close|proxim", ql) and lat and lng:
            result = self.facilities_within_radius(lat, lng, radius_km, specialty)
        elif re.search(r"nearest|closest|find.*near", ql) and lat and lng:
            result = self.nearest_facilities(lat, lng, specialty=specialty)
        elif re.search(r"desert|no.*access|unreachable", ql):
            result = self.identify_medical_deserts(specialty)
        elif re.search(r"gap|coverage|cold.?spot|underserved", ql):
            result = self.coverage_gap_analysis(specialty)
        elif re.search(r"equit|distribut|fair|balance|region.*compar", ql):
            result = self.regional_equity_analysis()
        elif re.search(r"distance.*between|how far", ql):
            cities = re.findall(r"(?:between|from)\s+(\w+).*?(?:and|to)\s+(\w+)", ql)
            if cities:
                result = self.distance_between_cities(cities[0][0], cities[0][1])
            else:
                result = self.regional_equity_analysis()
        else:
            result = self.coverage_gap_analysis(specialty)

        result["query"] = query
        result["duration_ms"] = round((time.time() - t0) * 1000, 2)
        return result
