from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.api.middleware.auth import verify_api_key
from src.models import (
    CallerCRMContext,
    CityRecommendationItem,
    ConciergeCategory,
    ConciergeRequest,
    GuestFeedback,
    GuestProfile,
    TravelPersona,
)
from src.repositories import get_guest_crm_repository, get_notification_repository
from src.services.guest_crm_service import GuestCRMService

router = APIRouter(
    prefix="/api/crm",
    tags=["Sina Hotels CRM"],
    dependencies=[Depends(verify_api_key)],
)


def get_guest_crm_service(request: Request) -> GuestCRMService:
    if hasattr(getattr(request, "app", None), "state"):
        svc = getattr(request.app.state, "crm_service", None)
        if svc is not None:
            return svc
    return GuestCRMService(
        crm_repo=get_guest_crm_repository(),
        notification_repo=get_notification_repository(),
        default_hotel_id="sina_bernini_bristol",
    )


class GuestPreferenceUpdate(BaseModel):
    dietary_restriction: str | None = None
    room_preference: str | None = None
    favorite_drink: str | None = None
    special_note: str | None = None
    persona: TravelPersona | None = None


class CreateConciergeRequestBody(BaseModel):
    phone: str
    category: ConciergeCategory
    title: str
    details: str
    scheduled_time: str | None = None


class SubmitFeedbackBody(BaseModel):
    phone: str
    nps_score: int = Field(ge=1, le=10)
    comments: str | None = None


@router.get("/guests", response_model=list[GuestProfile])
async def list_guests(
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Retrieve all guests in the CRM with VIP tiers and preferences."""
    return await service.crm_repo.get_all_guests()


@router.get("/caller-context", response_model=CallerCRMContext)
async def get_caller_context(
    phone: str = Query(..., description="Phone number to lookup"),
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Lookup incoming caller ID to provide guest context, stay stage, and greeting."""
    return await service.lookup_caller_context(phone)


@router.get("/guests/{phone}", response_model=GuestProfile)
async def get_guest_profile(
    phone: str,
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Retrieve full Guest 360 profile by phone number."""
    guest = await service.crm_repo.get_guest_by_phone(phone)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest profile not found")
    return guest


@router.post("/guests/{phone}/preferences", response_model=GuestProfile)
async def update_guest_preferences(
    phone: str,
    body: GuestPreferenceUpdate,
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Record guest preferences (allergies, room, drinks, latent persona)."""
    return await service.save_guest_preference(
        phone=phone,
        dietary_restriction=body.dietary_restriction,
        room_preference=body.room_preference,
        favorite_drink=body.favorite_drink,
        special_note=body.special_note,
        persona=body.persona,
    )


@router.post("/concierge/requests", response_model=ConciergeRequest)
async def create_concierge_request_endpoint(
    body: CreateConciergeRequestBody,
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Register a concierge service request (transport, dining, spa, city activity)."""
    return await service.create_concierge_request(
        phone=body.phone,
        category=body.category,
        title=body.title,
        details=body.details,
        scheduled_time=body.scheduled_time,
    )


@router.get("/recommendations", response_model=list[CityRecommendationItem])
async def get_recommendations(
    phone: str = Query(..., description="Guest phone to personalize recommendations"),
    category: ConciergeCategory | None = Query(None, description="Filter category"),
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Curated, persona-matched city and hotel recommendations."""
    return await service.get_personalized_recommendations(
        phone=phone,
        category=category,
    )


@router.post("/feedback", response_model=GuestFeedback)
async def submit_feedback_endpoint(
    body: SubmitFeedbackBody,
    service: GuestCRMService = Depends(get_guest_crm_service),
):
    """Record guest NPS and feedback, alerting management."""
    return await service.record_feedback(
        phone=body.phone,
        nps_score=body.nps_score,
        comments=body.comments,
    )
