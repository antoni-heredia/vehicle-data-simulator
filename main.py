import os
import time
import random
import requests
from geopy.distance import geodesic
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer


# --- Configuración de entorno ---
broker = os.getenv("KAFKA_BROKER", "kafka:9092")
topic = os.getenv("KAFKA_TOPIC", "vehicle-data")
schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
osrm_url = os.getenv("OSRM_URL", "http://osrm:5000")

origin = (-3.70379, 40.41678)  # Madrid
dest = (-0.37629, 39.46975)    # Valencia


# --- Obtener ruta OSRM ---
print(f"Solicitando ruta OSRM {origin} → {dest}")
r = requests.get(
    f"{osrm_url}/route/v1/driving/{origin[0]},{origin[1]};{dest[0]},{dest[1]}?overview=full&geometries=geojson"
)
r.raise_for_status()
coords = r.json()["routes"][0]["geometry"]["coordinates"]
print(f"Ruta obtenida: {len(coords)} puntos.")


# --- Conectar con Schema Registry ---
schema_registry_conf = {"url": schema_registry_url}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Leer los esquemas ya registrados
key_schema_str = schema_registry_client.get_latest_version("vehicle-data-key").schema.schema_str
value_schema_str = schema_registry_client.get_latest_version("vehicle-data-value").schema.schema_str

print("Usando esquemas desde Schema Registry: vehicle-data-key y vehicle-data-value")

# --- Crear serializers ---
key_serializer = AvroSerializer(schema_registry_client, key_schema_str)
value_serializer = AvroSerializer(schema_registry_client, value_schema_str)

# --- Configurar Producer moderno ---
producer_conf = {
    "bootstrap.servers": broker,
    "key.serializer": key_serializer,
    "value.serializer": value_serializer,
}
producer = SerializingProducer(producer_conf)

print(f"Iniciando simulación con {len(coords)} puntos")


# --- Enviar posiciones simuladas ---
for i in range(len(coords) - 1):
    start = (coords[i][1], coords[i][0])
    end = (coords[i + 1][1], coords[i + 1][0])
    dist_km = geodesic(start, end).km
    speed = random.uniform(70, 120)
    duration = (dist_km / speed) * 3600  # segundos

    key = {"vehicle_id": "car-001"}
    value = {
        "vehicle_id": "car-001",
        "lat": start[0],
        "lon": start[1],
        "speed_kmh": round(speed, 1),
        "rpm": int(speed * 40 + random.randint(-200, 200)),
        "oil_temp": round(70 + speed * 0.25 + random.uniform(-2, 2), 1),
        "fuel": round(50 - dist_km * 0.15, 2),
        "timestamp": int(time.time()),
    }

    print("Enviando:", value)
    producer.produce(topic=topic, key=key, value=value)
    producer.flush()
    print("Sent:", value)

    #time.sleep(max(1, duration)*0.001)  # acelerar la simulación

print("Finalizado.")
