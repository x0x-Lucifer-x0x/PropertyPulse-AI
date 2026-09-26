from typing import Optional, List
from pydantic import BaseModel


class PropertyOut(BaseModel):
    id: int
    name: str
    builder: str
    location: str
    nearby_locations: Optional[str] = None
    property_type: str
    bedrooms: int
    bathrooms: Optional[int] = None
    area_sqft: float
    price: float
    price_per_sqft: Optional[float] = None
    possession_date: Optional[str] = None
    rera_number: Optional[str] = None
    amenities: Optional[str] = None
    description: Optional[str] = None
    image_emoji: Optional[str] = "🏢"

    class Config:
        from_attributes = True


class PropertySearchParams(BaseModel):
    location: Optional[str] = None
    max_budget: Optional[float] = None
    min_budget: Optional[float] = None
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    minimum_area: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class MatchedProperty(BaseModel):
    property: PropertyOut
    match_score: int
    match_reasons: List[str]


class LeadQualification(BaseModel):
    score: int
    factors: List[str]
    next_action: str
    intent: str


class ChatResponse(BaseModel):
    reply: str
    properties: List[MatchedProperty] = []
    lead: Optional[LeadQualification] = None


class AffordabilityRequest(BaseModel):
    property_price: float
    down_payment: float
    interest_rate: float  # annual %, e.g. 8.5
    tenure_years: int


class AffordabilityResponse(BaseModel):
    loan_amount: float
    monthly_emi: float
    total_interest: float
    total_payment: float


class LeadQualifyRequest(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    timeline: Optional[str] = None
