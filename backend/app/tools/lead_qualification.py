from typing import Optional


def qualify_lead(
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    location: Optional[str] = None,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    timeline: Optional[str] = None,
) -> dict:
    """Deterministic, explainable lead scoring out of 100.

    This intentionally is NOT an LLM call — lead scoring should be
    consistent and auditable, not vary run to run.
    """
    score = 0
    factors = []

    if budget_min is not None or budget_max is not None:
        score += 25
        factors.append("Budget specified")
    else:
        factors.append("Budget not yet specified")

    if location:
        score += 20
        factors.append(f"Target location: {location}")
    else:
        factors.append("Location not yet specified")

    if bedrooms is not None:
        score += 15
        factors.append(f"Bedroom requirement: {bedrooms} BHK")

    if property_type:
        score += 10
        factors.append(f"Property type: {property_type}")

    timeline_l = (timeline or "").lower()
    if any(k in timeline_l for k in ["immediate", "asap", "urgent", "1 month", "within 1"]):
        score += 30
        intent = "High"
        factors.append("Urgent timeline signals strong intent")
    elif any(k in timeline_l for k in ["3 month", "6 month", "3-6", "few month"]):
        score += 20
        intent = "High"
        factors.append("Short-to-medium timeline signals good intent")
    elif any(k in timeline_l for k in ["year", "12 month", "not sure", "just looking", "browsing"]):
        score += 5
        intent = "Low"
        factors.append("Long or undefined timeline suggests early-stage interest")
    elif timeline:
        score += 10
        intent = "Medium"
        factors.append(f"Timeline: {timeline}")
    else:
        intent = "Medium"
        factors.append("Timeline not yet specified")

    score = max(0, min(100, score))

    if score >= 70:
        next_action = "Schedule a property site visit"
    elif score >= 45:
        next_action = "Send curated shortlist and follow up in 2-3 days"
    else:
        next_action = "Continue qualifying — ask about budget, location and timeline"

    return {
        "score": score,
        "factors": factors,
        "next_action": next_action,
        "intent": intent,
    }
