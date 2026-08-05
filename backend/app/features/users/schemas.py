from pydantic import BaseModel


class ImpactCategory(BaseModel):
    category: str
    weight_kg: float
    credits: float
    co2_kg: float


class ImpactMonth(BaseModel):
    month: str
    weight_kg: float


class ImpactBadge(BaseModel):
    code: str
    name: str
    icon: str
    earned: bool


class ImpactResponse(BaseModel):
    total_pickups: int
    total_kg_diverted: float
    co2_saved_kg: float
    credits_balance: float
    by_category: list[ImpactCategory]
    monthly_trend: list[ImpactMonth]
    badges: list[ImpactBadge]


class DeleteAccountRequest(BaseModel):
    reason: str | None = None


class ChatMessage(BaseModel):
    role: str  # "user", "bot", "model"
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessage]


__all__ = [
    "ImpactBadge",
    "ImpactCategory",
    "ImpactMonth",
    "ImpactResponse",
    "DeleteAccountRequest",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
]
