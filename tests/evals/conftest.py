import pytest

from src.config import settings
from src.repositories.memory_repo import (
    InMemoryBookingRepository,
    InMemoryNotificationRepository,
    InMemoryRestaurantRepository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.voice.agent import VoiceAgent
from src.voice.session import CallSession


@pytest.fixture(autouse=True)
def check_groq_api_key():
    """Skips eval tests if GROQ_API_KEY is not configured."""
    if not settings.GROQ_API_KEY:
        pytest.skip("GROQ_API_KEY is not configured. Skipping LLM evaluation test.")


@pytest.fixture
def eval_restaurant_repo():
    return InMemoryRestaurantRepository(restaurant_id="default_trattoria")


@pytest.fixture
def eval_booking_repo():
    return InMemoryBookingRepository()


@pytest.fixture
def eval_notification_repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def eval_availability_service(eval_restaurant_repo, eval_booking_repo):
    return AvailabilityService(
        restaurant_repo=eval_restaurant_repo,
        booking_repo=eval_booking_repo,
    )


@pytest.fixture
def eval_notification_service(eval_notification_repo):
    return NotificationService(notification_repo=eval_notification_repo)


@pytest.fixture
def eval_restaurant_service(eval_restaurant_repo):
    return RestaurantService(restaurant_repo=eval_restaurant_repo)


@pytest.fixture
def eval_booking_service(eval_booking_repo, eval_availability_service, eval_notification_service):
    return BookingService(
        booking_repo=eval_booking_repo,
        availability_service=eval_availability_service,
        notification_service=eval_notification_service,
    )


@pytest.fixture
def eval_agent(
    eval_availability_service,
    eval_booking_service,
    eval_restaurant_service,
    eval_notification_service,
):
    """Creates a real VoiceAgent instance wired to the live Groq LLM and test services."""
    return VoiceAgent(
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
        llm=None,  # Real Groq AsyncGroq LLM
        availability_service=eval_availability_service,
        booking_service=eval_booking_service,
        restaurant_service=eval_restaurant_service,
        notification_service=eval_notification_service,
    )


@pytest.fixture
def make_call_session():
    """Factory fixture generating isolated CallSessions for eval tests."""

    def _factory(
        call_id: str = "eval_call_1",
        caller_phone: str = "+39 333 1234567",
        caller_name: str = "Mario Rossi",
    ) -> CallSession:
        return CallSession(
            call_id=call_id,
            user_id=f"user_{caller_phone}",
            caller_phone=caller_phone,
            caller_name=caller_name,
            hotel_id="default_trattoria",
            hotel_name="Trattoria Bella Vista",
        )

    return _factory
