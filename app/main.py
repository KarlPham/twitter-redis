from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import init_db, close_db
from app.cache import init_cache, close_cache
from app.routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Mini Twitter API...")
    await init_db()
    await init_cache()
    print("All systems ready!")
    yield
    print("Shutting down...")
    await close_db()
    await close_cache()

app = FastAPI(title="Mini Twitter", lifespan=lifespan)

app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}