from sqlalchemy.orm import Session
from app.models import Property


def get_property_details(db: Session, property_id: int) -> Property | None:
    return db.query(Property).filter(Property.id == property_id).first()
