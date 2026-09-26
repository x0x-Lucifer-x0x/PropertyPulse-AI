from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    builder = Column(String, nullable=False)
    location = Column(String, nullable=False, index=True)
    nearby_locations = Column(String, nullable=True)  # comma-separated
    property_type = Column(String, nullable=False, index=True)  # Apartment, Villa, Plot, Row House
    bedrooms = Column(Integer, nullable=False, index=True)
    bathrooms = Column(Integer, nullable=True)
    area_sqft = Column(Float, nullable=False)
    price = Column(Float, nullable=False, index=True)  # in INR
    price_per_sqft = Column(Float, nullable=True)
    possession_date = Column(String, nullable=True)  # e.g. "Ready to move", "Dec 2026"
    rera_number = Column(String, nullable=True)
    amenities = Column(Text, nullable=True)  # comma-separated
    description = Column(Text, nullable=True)
    image_emoji = Column(String, nullable=True, default="🏢")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    property_type = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    intent = Column(String, nullable=True)  # Low / Medium / High
    score = Column(Integer, nullable=True)
    next_action = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
