from fastapi import APIRouter
from app.schemas import LeadQualifyRequest, AffordabilityRequest, AffordabilityResponse
from app.tools.lead_qualification import qualify_lead
from app.tools.affordability import calculate_affordability

router = APIRouter(prefix="/api", tags=["leads"])


@router.post("/leads/qualify")
def qualify(req: LeadQualifyRequest):
    return qualify_lead(
        budget_min=req.budget_min,
        budget_max=req.budget_max,
        location=req.location,
        bedrooms=req.bedrooms,
        property_type=req.property_type,
        timeline=req.timeline,
    )


@router.post("/affordability", response_model=AffordabilityResponse)
def affordability(req: AffordabilityRequest):
    return calculate_affordability(
        property_price=req.property_price,
        down_payment=req.down_payment,
        interest_rate=req.interest_rate,
        tenure_years=req.tenure_years,
    )
