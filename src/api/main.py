import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.agent.checkpointer import get_checkpointer
from src.api.routes.chat import router as chat_router
from src.api.routes.crm import router as crm_router
from src.api.routes.reservations import router as reservations_router
from src.api.routes.room_bookings import router as room_bookings_router
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(
    title="Sina Hotels AI Receptionist & CRM API",
    description="Deterministic voice receptionist and room reservation engine for Sina Bernini Bristol",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(room_bookings_router)
app.include_router(crm_router)
app.include_router(reservations_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "hotel": settings.DEFAULT_HOTEL_NAME,
        "environment": settings.ENVIRONMENT,
    }


# Mount built React frontend if dist exists
dist_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist",
)
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")

