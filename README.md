# Ticket Monitor Scraper

Extractor y monitor de carteleras de conciertos en Python. El proyecto simula un flujo ETL orientado al sector *ticketing*: extrae eventos desde metadatos estructurados (`JSON-LD`) y tarjetas HTML, normaliza precios/estados de disponibilidad y registra en SQLite cualquier cambio de precio o entradas agotadas (*Sold Out*).

## Arquitectura del proyecto

```text
ticket-monitor-scraper/
├── fixtures/
│   └── cartelera_madrid.html   # Maqueta HTML con eventos JSON-LD y tarjetas DOM
├── src/
│   ├── models.py               # Validación y limpieza de datos con Pydantic
│   ├── scraper.py              # Cliente HTTP con reintentos y parser híbrido
│   └── storage.py              # Persistencia en SQLite (UPSERT + historial) y CSV
├── tests/
│   └── test_scraper.py         # Suite de tests unitarios (pytest)
├── main.py                     # CLI principal con filtros de ejecución
└── requirements.txt