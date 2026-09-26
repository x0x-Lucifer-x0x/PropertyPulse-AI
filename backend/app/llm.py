import json
import logging
from typing import Optional
from groq import Groq
from sqlalchemy.orm import Session

from app.config import settings
from app.tools.search_properties import search_properties, compute_match
from app.tools.property_details import get_property_details
from app.tools.affordability import calculate_affordability
from app.tools.lead_qualification import qualify_lead

def _build_client():
    if not settings.groq_api_key:
        return None
    try:
        return Groq(api_key=settings.groq_api_key)
    except Exception:
        logging.getLogger("property_pulse").exception("Failed to initialize Groq client")
        return None


client = _build_client()

SYSTEM_PROMPT = """You are PropertyPulse AI, a real-estate sales assistant for a \
Bangalore property brokerage. You help prospective buyers find properties from \
the brokerage's own listed inventory, answer their questions, and gently \
qualify them as sales leads.

Rules you must follow strictly:
1. NEVER invent property facts (price, amenities, area, possession date, RERA \
   number, etc.). Only state facts returned by the search_properties or \
   get_property_details tools. If asked something not present in the data, say \
   plainly: "I don't have that information for this property."
2. Always call search_properties when the user describes what they're looking \
   for (location, budget, bedrooms, property type). Do not describe properties \
   from memory.
3. If a user's exact request has no matches (e.g. an unusual budget/location \
   combination), say so honestly and suggest the closest alternatives that the \
   tool actually returned.
4. Ask short, useful follow-up questions when key details (budget, location, \
   bedrooms, timeline) are missing — but don't interrogate the user with many \
   questions at once. One or two at a time.
5. When you have enough information (roughly: budget OR location, plus some \
   sense of timeline), call qualify_lead to produce a lead score, and mention \
   the recommended next step naturally in conversation.
6. Keep replies conversational and concise, like a helpful, knowledgeable \
   human sales assistant — not a robotic list of bullet points every time.
7. This is a demo product with demo data. If asked, be upfront that listings \
   are illustrative demo data, not live real-world inventory.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_properties",
            "description": "Search the property inventory by location, budget, bedrooms, property type and minimum area. Always use this before describing any properties to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Neighborhood/area, e.g. Whitefield"},
                    "max_budget": {"type": "number", "description": "Maximum budget in INR (e.g. 1 crore = 10000000)"},
                    "min_budget": {"type": "number", "description": "Minimum budget in INR"},
                    "bedrooms": {"type": "integer", "description": "Number of bedrooms (BHK)"},
                    "property_type": {"type": "string", "description": "Apartment, Villa, Plot, or Row House"},
                    "minimum_area": {"type": "number", "description": "Minimum carpet/built-up area in sq.ft."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_property_details",
            "description": "Get full details for one specific property by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {"type": "integer"},
                },
                "required": ["property_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_affordability",
            "description": "Calculate estimated monthly EMI and total interest for a home loan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_price": {"type": "number"},
                    "down_payment": {"type": "number"},
                    "interest_rate": {"type": "number", "description": "Annual interest rate as a percent, e.g. 8.5"},
                    "tenure_years": {"type": "integer"},
                },
                "required": ["property_price", "down_payment", "interest_rate", "tenure_years"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "qualify_lead",
            "description": "Score the current lead based on requirements gathered so far in the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_min": {"type": "number"},
                    "budget_max": {"type": "number"},
                    "location": {"type": "string"},
                    "bedrooms": {"type": "integer"},
                    "property_type": {"type": "string"},
                    "timeline": {"type": "string"},
                },
            },
        },
    },
]


def _run_tool(db: Session, name: str, args: dict):
    if name == "search_properties":
        results, fallback_used = search_properties(
            db,
            location=args.get("location"),
            max_budget=args.get("max_budget"),
            min_budget=args.get("min_budget"),
            bedrooms=args.get("bedrooms"),
            property_type=args.get("property_type"),
            minimum_area=args.get("minimum_area"),
        )
        matches = []
        for p in results:
            score, reasons = compute_match(p, args)
            matches.append({
                "id": p.id,
                "name": p.name,
                "location": p.location,
                "property_type": p.property_type,
                "bedrooms": p.bedrooms,
                "area_sqft": p.area_sqft,
                "price": p.price,
                "possession_date": p.possession_date,
                "match_score": score,
                "match_reasons": reasons,
            })
        return {
            "count": len(matches),
            "location_relaxed": fallback_used,
            "results": matches,
        }

    if name == "get_property_details":
        p = get_property_details(db, args.get("property_id"))
        if not p:
            return {"error": "Property not found"}
        return {
            "id": p.id,
            "name": p.name,
            "builder": p.builder,
            "location": p.location,
            "nearby_locations": p.nearby_locations,
            "property_type": p.property_type,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "area_sqft": p.area_sqft,
            "price": p.price,
            "price_per_sqft": p.price_per_sqft,
            "possession_date": p.possession_date,
            "rera_number": p.rera_number,
            "amenities": p.amenities,
            "description": p.description,
        }

    if name == "calculate_affordability":
        return calculate_affordability(
            property_price=args.get("property_price", 0),
            down_payment=args.get("down_payment", 0),
            interest_rate=args.get("interest_rate", 0),
            tenure_years=args.get("tenure_years", 0),
        )

    if name == "qualify_lead":
        return qualify_lead(
            budget_min=args.get("budget_min"),
            budget_max=args.get("budget_max"),
            location=args.get("location"),
            bedrooms=args.get("bedrooms"),
            property_type=args.get("property_type"),
            timeline=args.get("timeline"),
        )

    return {"error": f"Unknown tool {name}"}


def run_chat(db: Session, history: list[dict], user_message: str) -> dict:
    """Runs one turn of the agent loop: LLM -> tool calls -> DB -> LLM -> reply.
    Returns dict with 'reply', 'properties' (last search_properties results),
    and 'lead' (last qualify_lead result), for the frontend to render.
    """
    if client is None:
        return {
            "reply": (
                "PropertyPulse AI isn't configured yet — the backend is missing "
                "a GROQ_API_KEY. Add one to your .env file and restart the "
                "server to enable the AI assistant."
            ),
            "properties": [],
            "lead": None,
        }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    last_properties = []
    last_lead = None

    for _ in range(5):  # cap tool-call loop to avoid runaway
        try:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )
        except Exception:
            logging.getLogger("property_pulse").exception("Groq API call failed")
            return {
                "reply": (
                    "I'm having trouble reaching the AI service right now. "
                    "Please check that GROQ_API_KEY is valid and try again in a moment."
                ),
                "properties": last_properties,
                "lead": last_lead,
            }
        choice = completion.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return {
                "reply": msg.content or "",
                "properties": last_properties,
                "lead": last_lead,
            }

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _run_tool(db, tc.function.name, args)

            if tc.function.name == "search_properties":
                last_properties = result.get("results", [])
            if tc.function.name == "qualify_lead":
                last_lead = result

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    return {
        "reply": "I ran into trouble finishing that request — could you rephrase or simplify it?",
        "properties": last_properties,
        "lead": last_lead,
    }
