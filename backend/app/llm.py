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

SYSTEM_PROMPT = """You are PropertyPulse, a conversational assistant for a \
Bangalore property brokerage. You help people find homes from the \
brokerage's own listed inventory, answer their questions, and naturally \
build a sense of what they're looking for — but you are also just a \
capable, conversational AI, not a narrow bot that only understands real \
estate.

HOW TO READ INTENT
1. If the message is about properties, real estate, budgets, locations, \
   financing, or site visits: handle it with your tools against the real \
   database. Never describe or invent property facts (price, amenities, \
   area, possession date, RERA number, etc.) that didn't come from a tool \
   result — if something isn't in the data, say plainly: "I don't have \
   that information for this property."
2. If the message is a general question unrelated to real estate — coding, \
   math, writing, general knowledge, or anything else reasonable — just \
   answer it well, the way any competent assistant would. Do not deflect \
   with "I can only help with properties" or similar. Do not pretend an \
   unrelated question was about real estate.
3. If the conversation changes topic, follow where it goes. Don't steer it \
   back to property talk unless the person actually brings it back.
4. If the person returns to property-related questions later, pick the \
   real-estate context back up naturally, using whatever budget, location, \
   bedroom, or timeline details they already gave you earlier in the \
   conversation — don't ask for things they already told you.
5. If a request is ambiguous, ask one concise clarifying question rather \
   than guessing.
6. For anything you genuinely can't or shouldn't do, say briefly what's not \
   possible and, where there's a reasonable alternative, offer it.
7. Never introduce or describe yourself as "a real estate assistant" more \
   than once, and never repeat it as a boilerplate line — behave like a \
   normal, capable conversational partner throughout.

HOW TO HANDLE PROPERTY REQUESTS SPECIFICALLY
- Always call search_properties when someone describes what they're \
  looking for (location, budget, bedrooms, property type) rather than \
  answering from memory.
- If their exact request has no matches, say so honestly and suggest the \
  closest alternatives the tool actually returned.
- Ask short follow-up questions when key details (budget, location, \
  bedrooms, timeline) are missing — one or two at a time, not an \
  interrogation.
- Once you have a reasonable picture (roughly: budget or location, plus \
  some sense of timeline), call qualify_lead to score the lead and mention \
  the recommended next step naturally, not as a separate report.
- Keep replies conversational and concise, like a sharp, helpful human — \
  not a bulleted checklist by default.

WHEN TO USE search_knowledge_base
- For open-ended real-estate knowledge questions that aren't a structured \
  search: what RERA/BHK/EMI means, the difference between "ready to move" \
  and "under construction", or what a specific neighborhood is like.
- For descriptive or vibe-based property requests that plain filters \
  can't capture well, e.g. "something with a golf course view" or "a \
  quiet lakeside community" — use it alongside or instead of \
  search_properties.
- Answer only from what the tool actually returns. If it returns nothing \
  relevant, say you don't have that information rather than guessing.
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
            "name": "search_knowledge_base",
            "description": "Search general real-estate knowledge (RERA, BHK, EMI, possession status, Bangalore locality overviews) and descriptive/amenity-based property matches. Use for 'what is X' questions and vibe-based property requests that simple filters can't capture.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The question or descriptive request to search for"},
                },
                "required": ["query"],
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

    if name == "search_knowledge_base":
        from app.rag.index import get_index
        index = get_index(db)
        results = index.search(args.get("query", ""), k=4)
        return {"results": results}

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
