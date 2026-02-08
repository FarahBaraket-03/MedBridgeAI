"""
MedBridge AI — Test Queries
==============================
Exercises MUST HAVE queries from the hackathon spec plus
additional validation scenarios.

Usage:
  python -m src.test_queries
"""

import json
import time
from typing import Dict, List

from src.agents.genie_chat import GenieChatAgent
from src.agents.vector_search import VectorSearchAgent
from src.vectorize_and_store import get_qdrant_client, load_embedding_model


# ──────────────────────────────────────────────────────────────────────────────
# Test definitions — aligned with VF Agent MUST HAVE requirements
# ──────────────────────────────────────────────────────────────────────────────

GENIE_QUERIES = [
    # 1.1 — How many hospitals have cardiology?
    {
        "id": "1.1",
        "query": "How many hospitals have cardiology?",
        "category": "MUST_HAVE",
    },
    # 1.2 — How many hospitals in [region] can perform [procedure]?
    {
        "id": "1.2",
        "query": "How many hospitals in Greater Accra can perform cataract surgery?",
        "category": "MUST_HAVE",
    },
    # 1.5 — Which region has the most [Type] hospitals?
    {
        "id": "1.5",
        "query": "Which region has the most hospitals?",
        "category": "MUST_HAVE",
    },
    # 4.2 — High bed-to-doctor ratio anomalies
    {
        "id": "4.2",
        "query": "Which facilities have abnormal bed to doctor ratios?",
        "category": "SHOULD_HAVE",
    },
    # 4.7 — Correlations between facility characteristics
    {
        "id": "4.7",
        "query": "Show the distribution of specialties across all facilities.",
        "category": "MUST_HAVE",
    },
    # 7.5 — Single points of failure
    {
        "id": "7.5",
        "query": "Which procedures depend on very few facilities?",
        "category": "MUST_HAVE",
    },
    # Additional Genie queries
    {
        "id": "G.1",
        "query": "How many facilities are there in Kumasi?",
        "category": "BASIC",
    },
    {
        "id": "G.2",
        "query": "How many NGOs are in the dataset?",
        "category": "BASIC",
    },
    {
        "id": "G.3",
        "query": "Aggregate by region and show facility counts.",
        "category": "BASIC",
    },
]

VECTOR_QUERIES = [
    # 1.3 — What services does [Facility] offer?
    {
        "id": "1.3",
        "query": "What services does Korle Bu Teaching Hospital offer?",
        "category": "MUST_HAVE",
    },
    # 1.4 — Clinics in [Area] that do [Service]
    {
        "id": "1.4",
        "query": "Are there any clinics in Accra that do cataract surgery?",
        "category": "MUST_HAVE",
    },
    # Specialty search
    {
        "id": "V.1",
        "query": "Hospitals with orthopedic surgery capabilities",
        "category": "BASIC",
    },
    # NGO search
    {
        "id": "V.2",
        "query": "NGOs working on maternal and child health in Ghana",
        "category": "BASIC",
    },
    # Equipment search
    {
        "id": "V.3",
        "query": "Facilities with CT scanner or MRI equipment",
        "category": "BASIC",
    },
    # Emergency services
    {
        "id": "V.4",
        "query": "Emergency trauma centers in Northern Ghana",
        "category": "BASIC",
    },
    # Dental
    {
        "id": "V.5",
        "query": "Dental clinics in Kumasi",
        "category": "BASIC",
    },
    # 4.8 — High procedure breadth vs minimal infrastructure
    {
        "id": "4.8",
        "query": "Facilities claiming many procedures but with limited equipment",
        "category": "MUST_HAVE",
    },
    # 6.1 — Where is workforce for subspecialty?
    {
        "id": "6.1",
        "query": "Where are neurosurgeons practicing in Ghana?",
        "category": "MUST_HAVE",
    },
]


def _print_divider(char: str = "─", width: int = 80):
    print(char * width)


def _print_header(text: str):
    _print_divider("═")
    print(f"  {text}")
    _print_divider("═")


def run_genie_tests(genie: GenieChatAgent) -> List[Dict]:
    """Run all Genie Chat (Text2SQL) test queries."""
    results = []
    _print_header("GENIE CHAT (Text2SQL) QUERIES")

    for test in GENIE_QUERIES:
        print(f"\n[{test['id']}] ({test['category']}) Q: {test['query']}")
        _print_divider()
        t0 = time.time()
        try:
            result = genie.execute_query(test["query"])
            duration = (time.time() - t0) * 1000

            if isinstance(result, dict):
                pseudo_sql = result.get("pseudo_sql", "N/A")
                count = result.get("count", "N/A")
                data = result.get("data", result.get("results", []))
                print(f"  SQL:    {pseudo_sql}")
                print(f"  Count:  {count}")
                if isinstance(data, list):
                    for row in data[:5]:
                        if isinstance(row, dict):
                            compact = {k: v for k, v in row.items()
                                       if k not in ("document_text", "clinical_text", "specialty_text")}
                            print(f"    → {compact}")
                        else:
                            print(f"    → {row}")
                    if len(data) > 5:
                        print(f"    ... ({len(data)} total)")
                else:
                    print(f"  Result: {str(data)[:200]}")
            else:
                duration = (time.time() - t0) * 1000
                print(f"  Result: {str(result)[:300]}")

            results.append({"id": test["id"], "status": "OK", "ms": round(duration, 1)})
        except Exception as e:
            duration = (time.time() - t0) * 1000
            print(f"  ERROR: {e}")
            results.append({"id": test["id"], "status": "ERROR", "error": str(e), "ms": round(duration, 1)})

    return results


def run_vector_tests(vs: VectorSearchAgent) -> List[Dict]:
    """Run all Vector Search test queries."""
    results = []
    _print_header("VECTOR SEARCH QUERIES")

    for test in VECTOR_QUERIES:
        print(f"\n[{test['id']}] ({test['category']}) Q: {test['query']}")
        _print_divider()
        t0 = time.time()
        try:
            result = vs.search(test["query"], top_k=5)
            duration = result["duration_ms"]

            print(f"  Vector: {result['vector_used']}")
            print(f"  Filter: {result['filters_applied']}")
            print(f"  Found:  {result['count']} results ({duration}ms)")
            for r in result["results"][:5]:
                specs = ", ".join(r["specialties"][:3]) if r.get("specialties") else "N/A"
                score = r.get("score", 0)
                name = r.get("name", "?")
                city = r.get("city", "?")
                print(f"    [{score:.3f}] {name} ({city}) — {specs}")

            results.append({"id": test["id"], "status": "OK", "ms": round(duration, 1), "count": result["count"]})
        except Exception as e:
            duration = (time.time() - t0) * 1000
            print(f"  ERROR: {e}")
            results.append({"id": test["id"], "status": "ERROR", "error": str(e), "ms": round(duration, 1)})

    return results


def run_all():
    """Run all test queries and print summary."""
    print("\n" + "█" * 80)
    print("  MedBridge AI — Comprehensive Query Test Suite")
    print("█" * 80 + "\n")

    # Initialize agents
    print("Initializing agents...")
    client = get_qdrant_client()
    model = load_embedding_model()

    genie = GenieChatAgent()
    vs = VectorSearchAgent(client=client, model=model)

    # Run tests
    genie_results = run_genie_tests(genie)
    vector_results = run_vector_tests(vs)

    # Summary
    all_results = genie_results + vector_results
    ok = sum(1 for r in all_results if r["status"] == "OK")
    fail = sum(1 for r in all_results if r["status"] != "OK")
    avg_ms = sum(r["ms"] for r in all_results) / len(all_results) if all_results else 0

    _print_header("TEST SUMMARY")
    print(f"  Total:   {len(all_results)}")
    print(f"  Passed:  {ok}")
    print(f"  Failed:  {fail}")
    print(f"  Avg ms:  {avg_ms:.1f}")
    print()

    # Per-test summary table
    print(f"  {'ID':<6} {'Status':<8} {'ms':<8} {'Category'}")
    _print_divider()
    for test_def, result in zip(GENIE_QUERIES + VECTOR_QUERIES, all_results):
        status_icon = "✓" if result["status"] == "OK" else "✗"
        print(f"  {result['id']:<6} {status_icon} {result['status']:<6} {result['ms']:<8.1f} {test_def['category']}")

    if fail > 0:
        print(f"\n  Failed queries:")
        for r in all_results:
            if r["status"] != "OK":
                print(f"    [{r['id']}] {r.get('error', 'unknown')}")

    print()


if __name__ == "__main__":
    run_all()
