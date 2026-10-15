# Ticket Monitor Scraper

Extractor y monitor de carteleras de conciertos en Python. El proyecto implementa un flujo ETL orientado al sector *ticketing*: extrae eventos desde metadatos estructurados (`JSON-LD`) y tarjetas HTML, normaliza precios y estados de disponibilidad con `Pydantic` y registra en `SQLite` cualquier variación de precio o entradas agotadas (*Sold Out*).

## Estructura del proyecto

```text
ticket-monitor-scraper/
├── fixtures/
│   ├── cartelera_madrid.html   # Portal interactivo de conciertos (JSON-LD + tarjetas DOM + modal)
│   └── styles.css              # Hoja de estilos desacoplada de la maqueta HTML
├── src/
│   ├── models.py               # Esquema ConcertEvent y validadores de limpieza (Pydantic)
│   ├── scraper.py              # Cliente HTTP con reintentos (Backoff) y parser híbrido
│   └── storage.py              # Persistencia en SQLite (UPSERT + historial) y exportación CSV
├── tests/
│   └── test_scraper.py         # Suite de tests unitarios (pytest)
├── main.py                     # Punto de entrada CLI con filtros de ejecución
└── requirements.txt