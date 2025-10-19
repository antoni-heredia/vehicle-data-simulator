FROM python:3.12-slim

WORKDIR /app

# Instalar Poetry sin dependencias globales
RUN pip install --no-cache-dir poetry==1.8.3

# Copiar solo los archivos de definición de dependencias
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias en entorno del sistema (sin venv)
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

# Copiar el resto del código
COPY . .

ENV PYTHONUNBUFFERED=1 \
    KAFKA_BROKER=kafka:9092 \
    KAFKA_TOPIC=vehicle-data \
    OSRM_URL=http://osrm:5000 \
    OVERPASS_URL=https://overpass-api.de/api/interpreter \
    SCHEMA_REGISTRY_URL=http://schema-registry:8081

CMD ["poetry", "run", "python", "main.py"]
