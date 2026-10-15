import csv
import logging
import sqlite3
from pathlib import Path
from src.models import ConcertEvent

logger = logging.getLogger(__name__)


class TicketStorage:
    """
    Capa de persistencia encargada de guardar los eventos en SQLite y CSV,
    detectando y auditando cualquier cambio de precio o de estado (Sold Out).
    """

    def __init__(self, data_dir: str = "data"):
        """Crea el directorio de salida si no existe e inicializa el esquema SQLite."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "tickets.db"
        self._init_db()

    def _init_db(self) -> None:
        """
        Crea las tablas en SQLite si no existen:
        - 'events': estado actual de cada concierto (sin duplicados).
        - 'event_history': tabla de auditoría que registra fluctuaciones de precio y estado.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    old_price REAL,
                    new_price REAL,
                    old_status TEXT,
                    new_status TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events(event_id)
                )
            """)

    def upsert_to_sqlite(self, events: list[ConcertEvent]) -> None:
        """
        Inserta conciertos nuevos o actualiza los ya existentes (UPSERT).
        Si un concierto ya existía y ha cambiado su precio o disponibilidad,
        guarda el cambio en 'event_history' y lanza un aviso por consola.
        """
        if not events:
            return

        nuevos, actualizados = 0, 0
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            for ev in events:
                # 1. Consultar si el concierto ya existe en la base de datos
                cursor.execute(
                    "SELECT price_eur, status FROM events WHERE event_id = ?",
                    (ev.event_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    nuevos += 1
                else:
                    # 2. Si ya existía, comparar valores antiguos con los nuevos
                    old_price, old_status = row
                    price_changed = old_price != ev.price_eur
                    status_changed = old_status != ev.status.value

                    if price_changed or status_changed:
                        actualizados += 1
                        if status_changed:
                            logger.info(
                                f"🔔 [CAMBIO DE ESTADO] {ev.artist}: {old_status} -> {ev.status.value}"
                            )
                        if price_changed:
                            logger.info(
                                f"💶 [CAMBIO DE PRECIO] {ev.artist}: {old_price}€ -> {ev.price_eur}€"
                            )

                        # 3. Guardar registro de auditoría en la tabla histórica
                        cursor.execute("""
                            INSERT INTO event_history (
                                event_id, old_price, new_price, old_status, new_status
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            ev.event_id,
                            old_price,
                            ev.price_eur,
                            old_status,
                            ev.status.value,
                        ))

                # 4. Insertar o actualizar el estado actual del concierto (Idempotencia)
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
            f"SQLite sincronizado ({self.db_path}): {nuevos} nuevos, {actualizados} cambios auditados."
        )

    def export_to_csv(self, events: list[ConcertEvent], filename: str = "conciertos.csv") -> None:
        """Exporta la lista de conciertos validados a un archivo CSV limpio."""
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