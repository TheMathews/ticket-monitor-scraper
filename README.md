# Monitor de Conciertos y Disponibilidad de Tickets

Mini-pipeline ETL de *web scraping* diseñado para extraer carteleras de conciertos, normalizar precios/estados de disponibilidad y detectar variaciones (`Sold Out`, subidas de precio) en base de datos.

## Características Técnicas
- **Extracción Híbrida (`JSON-LD` + `DOM`):** Analiza metadatos estructurados `Schema.org/MusicEvent` (estándar en portales de ticketing) y tarjetas HTML con `BeautifulSoup4`.
- **Validación de Datos (`Pydantic v2`):** Limpieza automática de precios en formato europeo (`"Desde 28,50 € + gastos"` -> `28.5`) y normalización de estados (`AVAILABLE`, `LOW_TICKETS`, `SOLD_OUT`).
- **Persistencia con Detección de Cambios (`SQLite` + `CSV`):** Uso de sentencias `UPSERT` para no duplicar eventos y alertar en el log cuando un concierto cambia de precio o agota entradas.
- **Tolerancia a Fallos:** Los registros con HTML incompleto se omiten de forma controlada mediante `logging` sin detener el pipeline.

## Ejecución Rápida

```bash
pip install -r requirements.txt

# Ejecutar modo demostración (usa el snapshot HTML incluido en fixtures/)
python main.py

# Ejecutar tests unitarios
pytest -v