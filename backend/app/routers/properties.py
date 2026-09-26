from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Property
from app.schemas import PropertyOut, PropertySearchParams
from app.tools.search_properties import search_properties, compute_match

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=list[PropertyOut])
def list_properties(db: Session = Depends(get_db)):
    return db.query(Property).order_by(Property.price.asc()).all()


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.post("/search")
def search(params: PropertySearchParams, db: Session = Depends(get_db)):
    results, fallback_used = search_properties(
        db,
        location=params.location,
        max_budget=params.max_budget,
        min_budget=params.min_budget,
        bedrooms=params.bedrooms,
        property_type=params.property_type,
        minimum_area=params.minimum_area,
    )
    args = params.model_dump()
    matches = []
    for p in results:
        score, reasons = compute_match(p, args)
        matches.append({
            "property": PropertyOut.model_validate(p),
            "match_score": score,
            "match_reasons": reasons,
        })
    return {"count": len(matches), "location_relaxed": fallback_used, "results": matches}
