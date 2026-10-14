import csv
import logging
import sqlite3
from pathlib import Path
from src.models import ConcertEvent

logger = logging.getLogger(__name__)


class TicketStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "tickets.db"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    artist TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    event_date TEXT,
                    price_eur REAL,
                    status TEXT NOT NULL,
                    url TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def upsert_to_sqlite(self, events: list[ConcertEvent]) -> None:
        """Inserta nuevos eventos o actualiza existentes alertando si hay cambios."""
        if not events:
            return

        nuevos, actualizados = 0, 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for ev in events:
                cursor.execute(
                    "SELECT price_eur, status FROM events WHERE event_id = ?",
                    (ev.event_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    nuevos += 1
                else:
                    old_price, old_status = row
                    if old_status != ev.status.value:
                        logger.info(
                            f"🔔 [CAMBIO DE ESTADO] {ev.artist}: {old_status} -> {ev.status.value}"
                        )
                        actualizados += 1
                    if old_price != ev.price_eur:
                        logger.info(
                            f"💶 [CAMBIO DE PRECIO] {ev.artist}: {old_price}€ -> {ev.price_eur}€"
                        )
                        actualizados += 1

                cursor.execute("""
                    INSERT INTO events (event_id, artist, venue, event_date, price_eur, status, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        price_eur = excluded.price_eur,
                        status = excluded.status,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    ev.event_id,
                    ev.artist,
                    ev.venue,
                    ev.event_date,
                    ev.price_eur,
                    ev.status.value,
                    ev.url,
                ))
            conn.commit()

        logger.info(
            f"SQLite sincronizado ({self.db_path}): {nuevos} nuevos, {actualizados} con cambios."
        )

    def export_to_csv(self, events: list[ConcertEvent], filename: str = "conciertos.csv") -> None:
        if not events:
            return
        csv_path = self.data_dir / filename
        fieldnames = list(ConcertEvent.model_fields.keys())

        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ev in events:
                row = ev.model_dump()
                row["status"] = ev.status.value
                writer.writerow(row)

        logger.info(f"Exportados {len(events)} conciertos a {csv_path}")