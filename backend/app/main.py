from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import results, status, upload
from app.services.storage_service import init_db

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ZonaViva Spatial Analytics API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix=API_PREFIX)
app.include_router(status.router, prefix=API_PREFIX)
app.include_router(results.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "ok"}
