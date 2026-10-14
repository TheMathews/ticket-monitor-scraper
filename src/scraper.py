import json
import logging
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from src.models import ConcertEvent

logger = logging.getLogger(__name__)


class TicketScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9",
        })

    def fetch_page(self, url: str | None = None, local_file: str | None = None) -> str | None:
        """Obtiene el HTML desde una URL o desde un archivo local (modo offline/fallback)."""
        if local_file:
            path = Path(local_file)
            if path.exists():
                logger.info(f"Cargando HTML local desde: {path}")
                return path.read_text(encoding="utf-8")
            logger.error(f"No existe el archivo local: {path}")
            return None

        if not url:
            return None

        try:
            logger.info(f"Descargando cartelera desde: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(self.delay)
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error de red al consultar {url}: {e}")
            return None

    def parse_all_events(self, html: str) -> list[ConcertEvent]:
        """Combina eventos extraídos por JSON-LD y por tarjetas HTML sin duplicarlos."""
        events_by_id: dict[str, ConcertEvent] = {}

        for event in self._parse_json_ld(html) + self._parse_html_cards(html):
            events_by_id[event.event_id] = event

        return list(events_by_id.values())

    def _parse_json_ld(self, html: str) -> list[ConcertEvent]:
        """Extrae eventos de etiquetas <script type='application/ld+json'>."""
        soup = BeautifulSoup(html, "html.parser")
        events: list[ConcertEvent] = []

        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Event", "MusicEvent"):
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}

                        event = ConcertEvent(
                            event_id=str(item.get("identifier") or item.get("url")),
                            artist=item.get("name", ""),
                            venue=item.get("location", {}).get("name", "Recinto por confirmar"),
                            event_date=item.get("startDate", ""),
                            price_eur=offers.get("price"),
                            status=offers.get("availability", "AVAILABLE"),
                            url=offers.get("url") or item.get("url", ""),
                        )
                        events.append(event)
            except Exception as e:
                logger.warning(f"Bloque JSON-LD omitido por formato inválido: {e}")

        return events

    def _parse_html_cards(self, html: str) -> list[ConcertEvent]:
        """Extrae eventos de las tarjetas visuales <article class='event-card'>."""
        soup = BeautifulSoup(html, "html.parser")
        events: list[ConcertEvent] = []

        for card in soup.select("article.event-card"):
            try:
                event_id = card.get("data-event-id", "")
                artist_el = card.select_one(".event-artist")
                venue_el = card.select_one(".event-venue")
                time_el = card.select_one("time")
                price_el = card.select_one(".event-price")
                status_el = card.select_one(".ticket-status")
                link_el = card.select_one("a")

                if not (artist_el and venue_el and link_el):
                    raise ValueError("Faltan campos obligatorios (artista, recinto o enlace)")

                event = ConcertEvent(
                    event_id=event_id or link_el["href"],
                    artist=artist_el.get_text(strip=True),
                    venue=venue_el.get_text(strip=True),
                    event_date=time_el["datetime"] if time_el and time_el.has_attr("datetime") else "",
                    price_eur=price_el.get_text(strip=True) if price_el else None,
                    status=status_el.get_text(strip=True) if status_el else "AVAILABLE",
                    url=link_el["href"],
                )
                events.append(event)
            except Exception as e:
                card_id = card.get("data-event-id", "desconocido")
                logger.warning(f"Tarjeta '{card_id}' omitida: {e}")

        return events