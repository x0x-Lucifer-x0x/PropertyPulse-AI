from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, MatchedProperty, PropertyOut, LeadQualification
from app.llm import run_chat
from app.tools.property_details import get_property_details

router = APIRouter(prefix="/api", tags=["chat"])

# Simple in-memory conversation store keyed by session_id.
# Fine for a Phase 1 single-instance demo; would move to Redis/DB for
# multi-instance production deployments.
_CONVERSATIONS: dict[str, list[dict]] = {}
_MAX_HISTORY_TURNS = 12


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    history = _CONVERSATIONS.get(req.session_id, [])

    result = run_chat(db, history, req.message)

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": result["reply"]})
    _CONVERSATIONS[req.session_id] = history[-(_MAX_HISTORY_TURNS * 2):]

    matched_properties = []
    for m in result.get("properties", []):
        prop = get_property_details(db, m["id"])
        if prop:
            matched_properties.append(
                MatchedProperty(
                    property=PropertyOut.model_validate(prop),
                    match_score=m["match_score"],
                    match_reasons=m["match_reasons"],
                )
            )

    lead = None
    if result.get("lead"):
        l = result["lead"]
        lead = LeadQualification(
            score=l["score"], factors=l["factors"], next_action=l["next_action"], intent=l["intent"]
        )

    return ChatResponse(reply=result["reply"], properties=matched_properties, lead=lead)


@router.delete("/chat/{session_id}")
def reset_chat(session_id: str):
    _CONVERSATIONS.pop(session_id, None)
    return {"ok": True}
