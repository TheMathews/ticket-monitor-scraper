import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TicketStatus(str, Enum):
    """Estados posibles de disponibilidad de entradas para un concierto."""
    AVAILABLE = "AVAILABLE"
    LOW_TICKETS = "LOW_TICKETS"
    SOLD_OUT = "SOLD_OUT"


class ConcertEvent(BaseModel):
    """
    Modelo de validación para un concierto.
    Garantiza que cualquier dato extraído del HTML esté limpio y tipado
    antes de llegar a la base de datos o al CSV.
    """
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
        """
        Convierte textos de precios sucios (ej. 'Desde 28,50 € + gastos') en float (28.5).
        Si el concierto está agotado o no tiene precio numérico, devuelve None.
        """
        # Si ya viene como número o es nulo, se devuelve directamente
        if value is None or isinstance(value, (int, float)):
            return float(value) if value is not None else None

        # Estandarizar coma decimal europea a punto y extraer el primer número con regex
        cleaned = str(value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
        return float(match.group(0)) if match else None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str | TicketStatus) -> TicketStatus:
        """
        Unifica los distintos textos de disponibilidad de las webs de entradas
        (español, inglés o estándar Schema.org) dentro del Enum TicketStatus.
        """
        if isinstance(value, TicketStatus):
            return value

        text = str(value).lower().strip()

        # Detectar indicadores de entradas agotadas
        if any(w in text for w in ["agotado", "sold out", "outofstock", "no disponible"]):
            return TicketStatus.SOLD_OUT

        # Detectar indicadores de pocas entradas disponibles
        if any(w in text for w in ["últimas", "ultimas", "pocas", "limitedavailability"]):
            return TicketStatus.LOW_TICKETS

        # Por defecto, asumir entradas disponibles
        return TicketStatus.AVAILABLE