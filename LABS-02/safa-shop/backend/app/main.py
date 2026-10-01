import json
import os
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException


def read_secret(name: str, default: str | None = None) -> str | None:
    """Return the value of NAME_FILE (a Docker secret) if set, else the plain env var.

    Swarm mounts secrets as files under /run/secrets/. The official postgres and
    redis images use the same *_FILE convention; we mirror it here so the SAME
    app image runs unchanged under Compose (env vars) or Swarm (secret files).
    """
    file_path = os.environ.get(f"{name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as fh:
            return fh.read().strip()          # .strip() defuses the trailing-newline bug
    return os.environ.get(name, default)


POSTGRES_USER = read_secret("POSTGRES_USER")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD")
POSTGRES_DB = read_secret("POSTGRES_DB")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")

REDIS_PASSWORD = read_secret("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In Swarm there is no depends_on: postgres/redis may not be ready when this
    # container starts. If create_pool fails, the process exits non-zero and the
    # service's restart_policy brings it back — that retry loop IS the ordering.
    app.state.pg_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)
    yield
    await app.state.pg_pool.close()
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    async with app.state.pg_pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    await app.state.redis.ping()
    return {"status": "ok"}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    cache_key = f"product:{product_id}"
    cached = await app.state.redis.get(cache_key)
    if cached:
        payload = json.loads(cached)
        payload["source"] = "cache"
        return payload

    async with app.state.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, price_cents FROM products WHERE id = $1", product_id
        )
    if row is None:
        raise HTTPException(status_code=404, detail="product not found")

    payload = dict(row)
    await app.state.redis.set(cache_key, json.dumps(payload), ex=60)
    payload["source"] = "postgres"
    return payload