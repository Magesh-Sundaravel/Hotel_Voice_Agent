import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes.chat import router as chat_router
from src.api.routes.crm import router as crm_router
from src.api.routes.reservations import router as reservations_router
from src.api.routes.room_bookings import router as room_bookings_router
from src.api.routes.twilio_routes import router as twilio_router
from src.config import settings
from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.repositories import (
    get_booking_repository,
    get_guest_crm_repository,
    get_hotel_room_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.voice.agent import VoiceAgent

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    hotel_room_repo = get_hotel_room_repository()
    notification_repo = get_notification_repository()
    guest_crm_repo = get_guest_crm_repository()
    restaurant_repo = get_restaurant_repository()
    booking_repo = get_booking_repository()

    email_svc = EmailService()
    twilio_svc = TwilioService()

    notification_svc = NotificationService(
        notification_repo=notification_repo,
        email_service=email_svc,
        twilio_service=twilio_svc,
    )
    crm_svc = GuestCRMService(
        crm_repo=guest_crm_repo,
        notification_repo=notification_repo,
        default_hotel_id="sina_bernini_bristol",
    )
    hotel_booking_svc = HotelBookingService(
        room_repo=hotel_room_repo,
        notification_repo=notification_repo,
        guest_crm_service=crm_svc,
        twilio_service=twilio_svc,
        email_service=email_svc,
        hotel_id="sina_bernini_bristol",
    )
    restaurant_svc = RestaurantService(restaurant_repo)
    availability_svc = AvailabilityService(restaurant_repo, booking_repo)
    booking_svc = BookingService(
        booking_repo=booking_repo,
        availability_service=availability_svc,
        notification_service=notification_svc,
    )

    app.state.crm_service = crm_svc
    app.state.hotel_booking_service = hotel_booking_svc
    app.state.notification_service = notification_svc
    app.state.availability_service = availability_svc
    app.state.booking_service = booking_svc
    app.state.restaurant_service = restaurant_svc
    app.state.email_service = email_svc
    app.state.twilio_service = twilio_svc

    try:
        voice_agent = VoiceAgent(
            hotel_id="sina_bernini_bristol",
            hotel_name=settings.DEFAULT_HOTEL_NAME,
            hotel_booking_service=hotel_booking_svc,
            guest_crm_service=crm_svc,
            availability_service=availability_svc,
            booking_service=booking_svc,
            restaurant_service=restaurant_svc,
            notification_service=notification_svc,
            email_service=email_svc,
            twilio_service=twilio_svc,
        )
        app.state.voice_agent = voice_agent
        app.state.agent_graph = voice_agent  # Alias for backward compatibility
        logger.info("Successfully initialized VoiceAgent at app startup.")
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not pre-cache VoiceAgent at startup: %s", e)
        app.state.voice_agent = None
        app.state.agent_graph = None

    yield

    app.state.voice_agent = None
    app.state.agent_graph = None


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
app.include_router(twilio_router)


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
