from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Property


def search_properties(
    db: Session,
    location: Optional[str] = None,
    max_budget: Optional[float] = None,
    min_budget: Optional[float] = None,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    minimum_area: Optional[float] = None,
    limit: int = 8,
):
    """Executes a real query against the properties table. Falls back
    gracefully (dropping the location filter) if a location has zero
    exact matches, so the agent can offer alternatives instead of
    just saying 'no results'.
    """
    query = db.query(Property)

    if location:
        loc = location.strip().lower()
        query = query.filter(
            or_(
                Property.location.ilike(f"%{loc}%"),
                Property.nearby_locations.ilike(f"%{loc}%"),
            )
        )
    if max_budget is not None:
        query = query.filter(Property.price <= max_budget)
    if min_budget is not None:
        query = query.filter(Property.price >= min_budget)
    if bedrooms is not None:
        query = query.filter(Property.bedrooms == bedrooms)
    if property_type:
        query = query.filter(Property.property_type.ilike(f"%{property_type.strip()}%"))
    if minimum_area is not None:
        query = query.filter(Property.area_sqft >= minimum_area)

    results = query.order_by(Property.price.asc()).limit(limit).all()

    fallback_used = False
    if not results and location:
        # Retry without the location constraint so the agent can suggest alternatives
        fallback_used = True
        query = db.query(Property)
        if max_budget is not None:
            query = query.filter(Property.price <= max_budget)
        if min_budget is not None:
            query = query.filter(Property.price >= min_budget)
        if bedrooms is not None:
            query = query.filter(Property.bedrooms == bedrooms)
        if property_type:
            query = query.filter(Property.property_type.ilike(f"%{property_type.strip()}%"))
        results = query.order_by(Property.price.asc()).limit(limit).all()

    return results, fallback_used


def compute_match(prop: Property, params: dict) -> tuple[int, list[str]]:
    """Simple, explainable scoring — not a black box. Each criterion
    that matches adds points and a human-readable reason.
    """
    score = 40  # baseline for appearing in results at all
    reasons = []

    max_budget = params.get("max_budget")
    min_budget = params.get("min_budget")
    if max_budget is not None or min_budget is not None:
        in_range = True
        if max_budget is not None and prop.price > max_budget:
            in_range = False
        if min_budget is not None and prop.price < min_budget:
            in_range = False
        if in_range:
            score += 20
            reasons.append("Within your budget")
        else:
            reasons.append("Slightly outside your stated budget")

    location = params.get("location")
    if location:
        loc = location.strip().lower()
        if prop.location and loc in prop.location.lower():
            score += 20
            reasons.append(f"Located in {prop.location}")
        elif prop.nearby_locations and loc in prop.nearby_locations.lower():
            score += 10
            reasons.append(f"Close to {location.strip().title()}")

    bedrooms = params.get("bedrooms")
    if bedrooms is not None:
        if prop.bedrooms == bedrooms:
            score += 15
            reasons.append(f"{bedrooms} bedrooms as requested")
        else:
            reasons.append(f"{prop.bedrooms} BHK, not an exact match")

    property_type = params.get("property_type")
    if property_type and prop.property_type.lower() == property_type.strip().lower():
        score += 5
        reasons.append(f"Matches property type: {prop.property_type}")

    timeline = params.get("timeline")
    if timeline:
        possession = (prop.possession_date or "").lower()
        if "ready" in possession or "immediate" in possession:
            score += 5
            reasons.append("Ready to move, fits a short timeline")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("Matches your general search criteria")
    return score, reasons
