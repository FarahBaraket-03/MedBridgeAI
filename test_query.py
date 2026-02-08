"""Quick diagnostic: test the query pipeline end-to-end."""
import json, traceback
from backend.orchestration.graph import run_query

queries = [
    "How many hospitals offer cardiology services?",
    "Find facilities near Kumasi",
    "Where are the medical deserts in Ghana?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {q}")
    print('='*60)
    try:
        result = run_query(q)
        intent = result.get("intent", "?")
        agents = result.get("agents_used", [])
        resp = result.get("response", {})
        
        print(f"  Intent: {intent}")
        print(f"  Agents: {agents}")
        
        # Check for map facilities
        map_facs = resp.get("_map_facilities", [])
        print(f"  Map facilities: {len(map_facs)}")
        
        # Check multi-agent
        if resp.get("multi_agent_response"):
            for agent_name, data in resp.get("results", {}).items():
                action = data.get("action", data.get("scenario", "?"))
                count = data.get("count", data.get("total_found", data.get("anomalies_found", "?")))
                fac_count = len(data.get("facilities", data.get("results", data.get("stops", []))))
                print(f"    [{agent_name}] action={action} count={count} facs={fac_count}")
                # Check for lat/lng in facilities
                for key in ["facilities", "results", "stops", "flagged_facilities"]:
                    items = data.get(key, [])
                    if items and isinstance(items, list) and len(items) > 0:
                        has_coords = sum(1 for f in items if isinstance(f, dict) and (f.get("latitude") or f.get("lat")))
                        print(f"      {key}: {len(items)} items, {has_coords} with coords")
        else:
            action = resp.get("action", resp.get("scenario", "?"))
            count = resp.get("count", resp.get("total_found", "?"))
            print(f"  Action: {action}, Count: {count}")
            for key in ["facilities", "results", "stops", "deserts"]:
                items = resp.get(key, [])
                if items and isinstance(items, list) and len(items) > 0:
                    has_coords = sum(1 for f in items if isinstance(f, dict) and (f.get("latitude") or f.get("lat")))
                    print(f"    {key}: {len(items)} items, {has_coords} with coords")

        # Check trace for errors
        for t in result.get("trace", []):
            if t.get("agent") == "vector_search":
                print(f"  Vector search summary: {t.get('summary', '?')}")
                
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
