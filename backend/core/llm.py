"""
MedBridge AI — Groq Cloud LLM Integration
============================================
Provides natural-language synthesis for agent results.
Converts raw structured data into plain-English summaries
that non-technical NGO planners can understand and act on.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from groq import Groq

from backend.core.config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  GROQ CLIENT SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _call_groq(
    messages: List[Dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Call Groq chat completion with automatic fallback."""
    client = _get_client()

    for model in [GROQ_MODEL, GROQ_FALLBACK_MODEL]:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Groq model {model} failed: {e}")
            if model == GROQ_FALLBACK_MODEL:
                logger.error("All Groq models failed")
                raise
    return ""


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════════

SYNTHESIS_SYSTEM_PROMPT = """You are a healthcare intelligence assistant for the Virtue Foundation, an NGO working to improve healthcare access in Ghana.

Your job is to take structured data from multiple AI agents and produce a clear, actionable summary in plain English.

RULES:
1. Write for non-technical NGO planners — no code, no SQL, no technical jargon
2. Lead with the most important finding
3. Include specific numbers, facility names, and regions
4. Highlight actionable recommendations when applicable
5. Mention confidence levels and data quality concerns if relevant
6. Use bullet points for clarity
7. Keep it concise — aim for 3-8 sentences, max 200 words
8. If medical deserts or gaps are found, emphasize the human impact
9. Frame everything in terms of patient access and lives affected

EXAMPLES:
- Good: "There are 23 facilities offering cardiology services in Ghana, but 85% are concentrated in Greater Accra and Ashanti regions. Northern Region, with 2.8M people, has zero cardiology access — patients must travel 300+ km."
- Bad: "The query returned 23 rows from the database with specialty_id = 'cardiology'."

IMPORTANT: If there are suspicious claims or anomalies, explain them in terms NGO planners would understand (e.g., "This facility claims advanced surgery but appears to lack required equipment")."""


INTENT_SYSTEM_PROMPT = """You are a query classifier for a healthcare intelligence system analyzing Ghana's medical facilities.

Given a user query, determine the PRIMARY INTENT and which agents should handle it.

Available agents:
- genie: Structured data queries (counts, lists, filters, aggregations)
- vector_search: Semantic search in free-text medical records
- medical_reasoning: Validate capabilities, detect anomalies, check constraints
- geospatial: Distance, radius search, coverage gaps, medical deserts
- planning: Emergency routing, specialist deployment, resource allocation

Return a JSON object with:
{
  "intent": "brief description of what user wants",
  "agents": ["agent1", "agent2"],
  "reasoning": "one sentence why these agents"
}

Rules:
- Use 1-3 agents max
- If unsure, include vector_search as fallback
- Complex analytical queries should use multiple agents
- Simple count/list queries only need genie
- Questions about gaps/deserts need geospatial + medical_reasoning"""


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def synthesize_response(
    query: str,
    agent_results: List[Dict[str, Any]],
    trace: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
    intent: str = "",
) -> str:
    """
    Generate a plain-language summary of agent results for NGO planners.

    Args:
        query: Original user question
        agent_results: List of {agent: str, data: dict} from each agent
        trace: Execution trace entries
        citations: Row-level citations
        intent: Classified intent string

    Returns:
        Plain-English summary string
    """
    if not GROQ_API_KEY:
        return _fallback_synthesis(agent_results)

    # Build context from agent results
    context_parts = []
    for ar in agent_results:
        agent = ar.get("agent", "unknown")
        data = ar.get("data", {})
        # Truncate large result sets to avoid token limits
        summary = _truncate_data(data)
        context_parts.append(f"--- {agent.upper()} AGENT ---\n{json.dumps(summary, indent=2, default=str)}")

    agents_context = "\n\n".join(context_parts)

    # Add citation count
    citation_info = ""
    if citations:
        citation_info = f"\n\nCitations: {len(citations)} data points were used as evidence."

    user_msg = f"""User Question: "{query}"
Intent: {intent}

Agent Results:
{agents_context}
{citation_info}

Generate a clear, actionable summary for an NGO healthcare planner. Focus on what matters for patient access and resource allocation."""

    try:
        result = _call_groq(
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.3,
        )
        return result.strip()
    except Exception as e:
        logger.error(f"LLM synthesis failed: {e}")
        return _fallback_synthesis(agent_results)


def classify_intent_llm(query: str) -> Optional[Dict]:
    """
    Use LLM to classify query intent (fallback/enhancement for regex-based).

    Returns:
        Dict with {intent, agents, reasoning} or None if LLM fails
    """
    if not GROQ_API_KEY:
        return None

    try:
        result = _call_groq(
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            max_tokens=256,
            temperature=0.1,
        )

        # Parse JSON from response
        # Handle markdown code blocks
        cleaned = result.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"LLM intent classification failed: {e}")
        return None


def enhance_query(query: str) -> str:
    """
    Rewrite a vague or natural-language query into a more structured form
    while keeping the original intent. Helps match regex patterns better.
    """
    if not GROQ_API_KEY:
        return query

    try:
        result = _call_groq(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a query normalizer for a healthcare facility database in Ghana. "
                        "Rewrite the user's question to be clear and specific while preserving the original meaning. "
                        "If the query is already clear, return it unchanged. "
                        "Keep it as a single question. Do not explain — just return the rewritten query."
                    ),
                },
                {"role": "user", "content": query},
            ],
            max_tokens=128,
            temperature=0.1,
        )
        enhanced = result.strip().strip('"').strip("'")
        return enhanced if enhanced else query
    except Exception:
        return query


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _truncate_data(data: dict, max_items: int = 10) -> dict:
    """Truncate large result sets to fit within token limits."""
    truncated = {}
    for key, value in data.items():
        if isinstance(value, list) and len(value) > max_items:
            truncated[key] = value[:max_items]
            truncated[f"_{key}_note"] = f"Showing {max_items} of {len(value)} total"
        elif isinstance(value, dict) and len(str(value)) > 2000:
            # Truncate very large nested dicts
            truncated[key] = {k: v for i, (k, v) in enumerate(value.items()) if i < 10}
            truncated[f"_{key}_note"] = "Truncated for brevity"
        else:
            truncated[key] = value
    return truncated


def _fallback_synthesis(agent_results: List[Dict[str, Any]]) -> str:
    """Generate a basic summary without LLM when Groq is unavailable."""
    parts = []
    for ar in agent_results:
        agent = ar.get("agent", "unknown")
        data = ar.get("data", {})

        if agent == "genie":
            count = data.get("count")
            action = data.get("action", "query")
            if count is not None:
                parts.append(f"Found {count} matching facilities.")
            else:
                results = data.get("results", [])
                parts.append(f"Retrieved {len(results)} results.")

        elif agent == "vector_search":
            results = data.get("results", [])
            parts.append(f"Found {len(results)} semantically matching facilities.")

        elif agent == "medical_reasoning":
            action = data.get("action", "")
            if action == "anomaly_detection":
                parts.append(f"Detected {data.get('anomalies_found', 0)} anomalies out of {data.get('total_checked', 0)} facilities.")
            elif action == "constraint_validation":
                parts.append(f"Validated {data.get('total_checked', 0)} facilities; {data.get('facilities_with_issues', 0)} have potential issues.")
            elif action == "coverage_gap_analysis":
                parts.append(f"Found {data.get('gaps_found', 0)} coverage gaps for {data.get('specialty', 'healthcare')}.")
            elif action == "red_flag_detection":
                parts.append(f"Flagged {data.get('facilities_flagged', 0)} facilities with suspicious claims.")
            elif action == "single_point_of_failure":
                parts.append(f"Identified {data.get('critical_specialties', 0)} specialties with critical dependency risks.")
            else:
                parts.append("Medical analysis complete.")

        elif agent == "geospatial":
            action = data.get("action", "")
            if action == "medical_desert_detection":
                parts.append(f"Identified {data.get('deserts_found', 0)} medical deserts.")
            elif action == "facilities_within_radius":
                parts.append(f"Found {data.get('total_found', 0)} facilities within {data.get('radius_km', 0)} km.")
            elif action == "coverage_gap_analysis":
                parts.append(f"Coverage is {data.get('coverage_percentage', 0)}% with {data.get('cold_spots_found', 0)} cold spots.")
            else:
                parts.append("Geospatial analysis complete.")

        elif agent == "planning":
            parts.append(data.get("title", "Planning analysis complete."))

    return " ".join(parts) if parts else "Analysis complete."
