import argparse
import logging
from src.models import TicketStatus
from src.scraper import TicketScraper
from src.storage import TicketStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor de Conciertos y Disponibilidad de Entradas"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL de la cartelera a raspar (si se omite, usa el fixture local)",
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default="fixtures/cartelera_madrid.html",
        help="Ruta al archivo HTML local de respaldo",
    )
    parser.add_argument(
        "--max-price",
        type=float,
        default=None,
        help="Filtra conciertos cuyo precio sea menor o igual al indicado (en EUR)",
    )
    parser.add_argument(
        "--only-available",
        action="store_true",
        help="Excluye conciertos agotados (SOLD_OUT)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scraper = TicketScraper(delay=1.0)
    storage = TicketStorage(data_dir="data")

    if args.url:
        html = scraper.fetch_page(url=args.url)
    else:
        html = scraper.fetch_page(local_file=args.fixture)

    if not html:
        logger.error("No se pudo obtener contenido HTML. Abortando ejecución.")
        return

    events = scraper.parse_all_events(html)
    logger.info(f"Extraídos y validados {len(events)} eventos del HTML.")

    if args.only_available:
        events = [e for e in events if e.status != TicketStatus.SOLD_OUT]
        logger.info(f"Filtro --only-available activo: quedan {len(events)} eventos con entradas.")

    if args.max_price is not None:
        events = [
            e for e in events
            if e.price_eur is not None and e.price_eur <= args.max_price
        ]
        logger.info(f"Filtro --max-price ({args.max_price}€) activo: quedan {len(events)} eventos.")

    storage.upsert_to_sqlite(events)
    storage.export_to_csv(events)


if __name__ == "__main__":
    main()