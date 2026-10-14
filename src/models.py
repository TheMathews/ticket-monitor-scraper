import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TicketStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LOW_TICKETS = "LOW_TICKETS"
    SOLD_OUT = "SOLD_OUT"


class ConcertEvent(BaseModel):
    event_id: str = Field(..., min_length=1)
    artist: str = Field(..., min_length=1)
    venue: str = Field(..., min_length=1)
    event_date: str
    price_eur: float | None = Field(default=None, ge=0)
    status: TicketStatus = TicketStatus.AVAILABLE
    url: str

    @field_validator("price_eur", mode="before")
    @classmethod
    def clean_price(cls, value: str | float | int | None) -> float | None:
        if value is None or isinstance(value, (int, float)):
            return float(value) if value is not None else None
        # Reemplaza coma europea por punto y busca el primer número decimal
        cleaned = str(value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
        return float(match.group(0)) if match else None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str | TicketStatus) -> TicketStatus:
        if isinstance(value, TicketStatus):
            return value
        text = str(value).lower().strip()
        if any(w in text for w in ["agotado", "sold out", "outofstock", "no disponible"]):
            return TicketStatus.SOLD_OUT
        if any(w in text for w in ["últimas", "ultimas", "pocas", "limitedavailability"]):
            return TicketStatus.LOW_TICKETS
        return TicketStatus.AVAILABLE