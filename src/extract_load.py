import os
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CITIES = {
    "Portland": (45.52, -122.68),
    "New York": (40.71, -74.01),
    "Shanghai": (31.23, 121.47),
    "Beijing": (39.90, 116.41),
}
API_URL = "https://api.open-meteo.com/v1/forecast"

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.weather_hourly (
    city            TEXT        NOT NULL,
    ts              TIMESTAMP   NOT NULL,
    temperature_2m  DOUBLE PRECISION,
    precipitation   DOUBLE PRECISION,
    wind_speed_10m  DOUBLE PRECISION,
    loaded_at       TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (city, ts)
);
"""

UPSERT = """
INSERT INTO raw.weather_hourly
    (city, ts, temperature_2m, precipitation, wind_speed_10m)
VALUES %s
ON CONFLICT (city, ts) DO UPDATE SET
    temperature_2m = EXCLUDED.temperature_2m,
    precipitation  = EXCLUDED.precipitation,
    wind_speed_10m = EXCLUDED.wind_speed_10m,
    loaded_at      = now();
"""


def extract(city, lat, lon, past_days=7):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m",
        "past_days": past_days,
        "timezone": "UTC",
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    h = resp.json()["hourly"]
    return [
        (city, t, temp, prec, wind)
        for t, temp, prec, wind in zip(
            h["time"], h["temperature_2m"], h["precipitation"], h["wind_speed_10m"]
        )
    ]


def load(rows):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    with conn, conn.cursor() as cur:
        cur.execute(DDL)
        execute_values(cur, UPSERT, rows)
    conn.close()


if __name__ == "__main__":
    for city, (lat, lon) in CITIES.items():
        rows = extract(city, lat, lon)
        load(rows)
        logging.info("Loaded %d rows for %s", len(rows), city)
