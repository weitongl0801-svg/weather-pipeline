# Weather Data Pipeline

An end-to-end data engineering project that ingests hourly weather data from the
[Open-Meteo API](https://open-meteo.com/) into a PostgreSQL warehouse.

## Architecture

Open-Meteo API -> Python extract/load -> PostgreSQL (raw layer)

Coming next: dbt transformations, Airflow orchestration, data quality tests, CI, dashboard.

## Tech stack

Python, PostgreSQL 16, Docker Compose

## Features

- Pulls 14 days of hourly data (7 past + 7 forecast) for 4 cities
- Idempotent loads: primary key (city, ts) + ON CONFLICT DO UPDATE, so re-running never creates duplicates
- Raw layer kept untransformed, with a loaded_at audit column

## Quick start

1. Copy the example env file: `cp .env.example .env`
2. Start Postgres: `docker compose up -d`
3. Create a virtualenv: `python3 -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the pipeline: `python src/extract_load.py`
