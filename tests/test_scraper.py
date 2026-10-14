import sqlite3
from src.models import ConcertEvent, TicketStatus
from src.scraper import TicketScraper
from src.storage import TicketStorage


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
    assert len(events) == 4
    artists = {e.artist for e in events}
    assert "Vetusta Morla - Fin de Gira" in artists
    assert "Carolina Durante" in artists


def test_sqlite_upsert_and_history_audit(tmp_path):
    storage = TicketStorage(data_dir=str(tmp_path))

    # 1ª ejecución: el concierto sale a la venta a 25€
    initial_event = ConcertEvent(
        event_id="evt-999",
        artist="Artista Test",
        venue="Sala Test",
        event_date="2026-12-01",
        price_eur=25.0,
        status=TicketStatus.AVAILABLE,
        url="https://ejemplo.com/999",
    )
    storage.upsert_to_sqlite([initial_event])

    # 2ª ejecución: sube a 30€ y pasa a últimas entradas
    updated_event = ConcertEvent(
        event_id="evt-999",
        artist="Artista Test",
        venue="Sala Test",
        event_date="2026-12-01",
        price_eur=30.0,
        status=TicketStatus.LOW_TICKETS,
        url="https://ejemplo.com/999",
    )
    storage.upsert_to_sqlite([updated_event])

    # Comprobar que la tabla event_history ha registrado el cambio
    with sqlite3.connect(storage.db_path) as conn:
        row = conn.execute(
            "SELECT old_price, new_price, old_status, new_status FROM event_history WHERE event_id = 'evt-999'"
        ).fetchone()

    assert row == (25.0, 30.0, "AVAILABLE", "LOW_TICKETS")