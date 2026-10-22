from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.checkpointer import get_checkpointer
from src.api.routes.chat import router as chat_router
from src.api.routes.reservations import router as reservations_router
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(
    title="Italian Restaurant AI Receptionist API",
    description="Deterministic voice receptionist and reservation engine for Trattoria Bella Vista",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reservations_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "restaurant": settings.DEFAULT_RESTAURANT_NAME,
        "environment": settings.ENVIRONMENT,
    }
