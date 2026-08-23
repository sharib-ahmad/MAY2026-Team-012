import logging
import os

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Import SQLAlchemy model registry to prevent Mapper errors
from app.features.collection_ops.models import Pickup
from app.features.complaints.models import Ticket
from app.features.credits.models import Credit, CreditFactor, UserBadge
from app.features.reuse.models import ReuseClaim, ReuseListing
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.features.users.schemas import ChatMessage
from app.models.enums import CreditStatus
from app.core.config import get_settings

logger = logging.getLogger("verdeza")

SYSTEM_INSTRUCTION = """You are EcoBot, the official Verdeza AI assistant.
Your primary role is to help citizens with waste management, recycling, eco-credits,
and their account details.
You are strictly limited to discussing topics related to:
1. Waste management and segregation (e.g. wet waste, dry waste, hazardous waste).
2. The Verdeza eco-credit system (earning credits, CO2 savings, badges).
3. The Community Shelf (reuse listings, claims).
4. The user's own data in Verdeza (their pickups, tickets, listings, claims, credits, and badges).
5. Ward management, zones, and Verdeza features.

CRITICAL RULES:
- If the user asks a question about any other topic (such as general knowledge, programming,
  sports, non-Verdeza politics, science, math, cooking recipes, writing code, or anything
  unrelated to waste management, recycling, eco-credits, and Verdeza), you MUST politely refuse
  to answer. Say: 'I am only able to help you with questions related to waste management,
  recycling, and your activities in Verdeza.'
- You MUST only use the provided tool functions to access database records. Do not invent,
  hallucinate, or assume any pickup references, tickets, credits, or listing details.
  If a tool returns no data, inform the user that you couldn't find any records.
- You only have access to the current citizen's own data. Never share information about
  other users.
- Be concise, helpful, and polite. Use clear markdown formatting in your responses.
"""


def get_my_pickups(db: Session, user_id) -> dict:
    stmt = (
        select(Pickup)
        .where(Pickup.citizen_id == user_id)
        .order_by(Pickup.created_at.desc())
        .limit(5)
    )
    pickups = db.scalars(stmt).all()
    result = []
    for p in pickups:
        result.append(
            {
                "ref_code": p.ref_code,
                "category": p.category,
                "status": str(p.status.value) if hasattr(p.status, "value") else str(p.status),
                "scheduled_date": p.scheduled_date.isoformat() if p.scheduled_date else None,
                "estimated_weight": float(p.estimated_weight),
                "actual_weight": float(p.actual_weight) if p.actual_weight is not None else None,
                "credits_earned": float(p.credits_earned),
                "co2_saved": float(p.co2_saved),
                "is_contaminated": p.is_contaminated,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
        )
    return {"pickups": result}


def get_my_tickets(db: Session, user_id) -> dict:
    stmt = (
        select(Ticket)
        .where(Ticket.raised_by_id == user_id)
        .order_by(Ticket.created_at.desc())
        .limit(5)
    )
    tickets = db.scalars(stmt).all()
    result = []
    for t in tickets:
        result.append(
            {
                "ref_code": t.ref_code,
                "issue_type": str(t.issue_type.value)
                if hasattr(t.issue_type, "value")
                else str(t.issue_type),
                "status": str(t.status.value) if hasattr(t.status, "value") else str(t.status),
                "description": t.description,
                "resolution_notes": t.resolution_notes,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        )
    return {"tickets": result}


def get_my_impact_and_credits(db: Session, user_id) -> dict:
    credits_sum = db.scalar(
        select(func.sum(Credit.amount)).where(
            Credit.user_id == user_id, Credit.status == CreditStatus.CONFIRMED
        )
    )
    co2_sum = db.scalar(
        select(func.sum(Credit.co2_saved)).where(
            Credit.user_id == user_id, Credit.status == CreditStatus.CONFIRMED
        )
    )

    badges_stmt = select(UserBadge).where(UserBadge.user_id == user_id)
    user_badges = db.scalars(badges_stmt).all()
    badges_list = []
    for ub in user_badges:
        badges_list.append(
            {
                "code": ub.badge.code,
                "name": ub.badge.name,
                "category": str(ub.badge.category.value)
                if hasattr(ub.badge.category, "value")
                else str(ub.badge.category),
                "description": ub.badge.description,
                "earned_at": ub.earned_at.isoformat() if ub.earned_at else None,
            }
        )

    return {
        "total_credits": float(credits_sum) if credits_sum is not None else 0.0,
        "total_co2_saved": float(co2_sum) if co2_sum is not None else 0.0,
        "badges_earned": badges_list,
    }


def get_my_reuse_items(db: Session, user_id) -> dict:
    listings_stmt = (
        select(ReuseListing)
        .where(ReuseListing.lister_id == user_id)
        .order_by(ReuseListing.created_at.desc())
        .limit(5)
    )
    listings = db.scalars(listings_stmt).all()
    listings_list = []
    for rl in listings:
        listings_list.append(
            {
                "title": rl.title,
                "category": str(rl.category.value)
                if hasattr(rl.category, "value")
                else str(rl.category),
                "condition": str(rl.condition.value)
                if hasattr(rl.condition, "value")
                else str(rl.condition),
                "status": str(rl.status.value) if hasattr(rl.status, "value") else str(rl.status),
                "rejection_reason": rl.rejection_reason,
                "created_at": rl.created_at.isoformat() if rl.created_at else None,
            }
        )

    claims_stmt = (
        select(ReuseClaim)
        .where(ReuseClaim.claimant_id == user_id)
        .order_by(ReuseClaim.created_at.desc())
        .limit(5)
    )
    claims = db.scalars(claims_stmt).all()
    claims_list = []
    for rc in claims:
        claims_list.append(
            {
                "listing_title": rc.listing.title if rc.listing else "Unknown",
                "status": str(rc.status.value) if hasattr(rc.status, "value") else str(rc.status),
                "note": rc.note,
                "decided_at": rc.decided_at.isoformat() if rc.decided_at else None,
                "created_at": rc.created_at.isoformat() if rc.created_at else None,
            }
        )

    return {"my_listings": listings_list, "my_claims": claims_list}


def get_waste_rules_and_rates(db: Session, user_id) -> dict:
    stmt = (
        select(WasteCategory, CreditFactor)
        .join(CreditFactor, WasteCategory.code == CreditFactor.category, isouter=True)
        .where(WasteCategory.is_active)
    )

    rows = db.execute(stmt).all()
    categories_list = []
    for cat, factor in rows:
        categories_list.append(
            {
                "code": cat.code,
                "label": cat.label,
                "credit_rate": float(factor.credit_rate) if factor else 0.0,
                "co2_factor": float(factor.co2_factor) if factor else 0.0,
                "description": factor.description if factor else None,
            }
        )
    return {"waste_categories": categories_list}


TOOL_MAP = {
    "get_my_pickups": get_my_pickups,
    "get_my_tickets": get_my_tickets,
    "get_my_impact_and_credits": get_my_impact_and_credits,
    "get_my_reuse_items": get_my_reuse_items,
    "get_waste_rules_and_rates": get_waste_rules_and_rates,
}


async def execute_chatbot_turn(
    message: str, history: list[ChatMessage], current_user: User, db: Session
) -> dict:

    api_key = get_settings().GEMINI_API_KEY
    if not api_key:
        return {
            "reply": (
                "EcoBot is currently undergoing maintenance "
                "(Gemini API key is not configured). Please try again later."
            ),
            "history": history
            + [
                ChatMessage(role="user", text=message),
                ChatMessage(role="bot", text="Maintenance Mode: API key missing."),
            ],
        }

    contents = []
    for msg in history:
        role = "model" if msg.role in ("bot", "model") else "user"
        contents.append({"role": role, "parts": [{"text": msg.text}]})

    contents.append({"role": "user", "parts": [{"text": message}]})

    gemini_tools = [
        {
            "functionDeclarations": [
                {
                    "name": "get_my_pickups",
                    "description": (
                        "Retrieve recent waste pickups of the logged-in citizen. "
                        "Returns details like ref_code, category (WET, DRY, HAZARDOUS), "
                        "status, scheduled date, actual weight, credits earned, and co2 saved."
                    ),
                    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
                },
                {
                    "name": "get_my_tickets",
                    "description": (
                        "Retrieve recent grievance tickets raised by the logged-in citizen. "
                        "Returns details like ref_code, issue_type, status, description, "
                        "resolution_notes, and created_at."
                    ),
                    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
                },
                {
                    "name": "get_my_impact_and_credits",
                    "description": (
                        "Retrieve the logged-in citizen's total eco-credits, "
                        "total carbon dioxide (CO2) saved, and list of earned badges."
                    ),
                    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
                },
                {
                    "name": "get_my_reuse_items",
                    "description": (
                        "Retrieve the citizen's own community shelf reuse listings and claims. "
                        "Returns details like listing titles, categories, condition, and status."
                    ),
                    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
                },
                {
                    "name": "get_waste_rules_and_rates",
                    "description": (
                        "Retrieve the official waste categories, their credit rates "
                        "(credits per kg), and CO2 saving factors."
                    ),
                    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
                },
            ]
        }
    ]

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "tools": gemini_tools,
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.5-flash:generateContent?key={api_key}"
    )

    max_turns = 5
    async with httpx.AsyncClient(timeout=30.0) as client:
        for _turn in range(max_turns):
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Gemini API returned error {response.status_code}: {response.text}")
                return {
                    "reply": (
                        "I encountered an error trying to process your request. Please try again."
                    ),
                    "history": history
                    + [
                        ChatMessage(role="user", text=message),
                        ChatMessage(role="bot", text="Error communicating with LLM."),
                    ],
                }

            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates:
                return {
                    "reply": "I'm sorry, I couldn't formulate a response.",
                    "history": history
                    + [
                        ChatMessage(role="user", text=message),
                        ChatMessage(role="bot", text="No candidates returned."),
                    ],
                }

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]

            if not function_calls:
                text_response = "".join(p.get("text", "") for p in parts if p.get("text"))
                updated_history = history + [
                    ChatMessage(role="user", text=message),
                    ChatMessage(role="bot", text=text_response),
                ]
                return {"reply": text_response, "history": updated_history}

            payload["contents"].append(content)

            function_responses = []
            for fc in function_calls:
                name = fc.get("name")
                tool_func = TOOL_MAP.get(name)
                if tool_func:
                    try:
                        tool_result = tool_func(db, current_user.id)
                    except Exception as e:
                        logger.exception(f"Error executing chatbot tool {name}")
                        tool_result = {"error": str(e)}
                else:
                    tool_result = {"error": "Function not found"}

                function_responses.append(
                    {"functionResponse": {"name": name, "response": tool_result}}
                )

            payload["contents"].append({"role": "function", "parts": function_responses})

        return {
            "reply": (
                "I apologize, but I had trouble resolving that query within "
                "a safe number of steps. Could you try asking in a simpler way?"
            ),
            "history": history
            + [
                ChatMessage(role="user", text=message),
                ChatMessage(role="bot", text="Max turns exceeded."),
            ],
        }
