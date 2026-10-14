from src.models import ConcertEvent, TicketStatus
from src.scraper import TicketScraper


def test_price_and_status_normalization():
    event = ConcertEvent(
        event_id="evt-100",
        artist="Banda de Prueba",
        venue="Sala Sol",
        event_date="2026-11-01",
        price_eur="Desde 22,90 € + gastos",
        status="¡Últimas entradas!",
        url="https://ejemplo.com/100",
    )
    assert event.price_eur == 22.90
    assert event.status == TicketStatus.LOW_TICKETS


def test_sold_out_without_numeric_price():
    event = ConcertEvent(
        event_id="evt-101",
        artist="Banda Agotada",
        venue="La Riviera",
        event_date="2026-11-02",
        price_eur="No disponible",
        status="Sold Out",
        url="https://ejemplo.com/101",
    )
    assert event.price_eur is None
    assert event.status == TicketStatus.SOLD_OUT


def test_hybrid_html_and_json_ld_parsing():
    scraper = TicketScraper()
    html = scraper.fetch_page(local_file="fixtures/cartelera_madrid.html")
    assert html is not None

    events = scraper.parse_all_events(html)
    # Deben salir 4 eventos válidos y descartarse el evento corrupto sin lanzar excepción
    assert len(events) == 4
    artists = {e.artist for e in events}
    assert "Vetusta Morla - Fin de Gira" in artists
    assert "Carolina Durante" in artists