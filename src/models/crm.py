from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class TravelPersona(StrEnum):
    ROMANTIC_COUPLE = "romantic_couple"
    BUSINESS_SOLO = "business_solo"
    FAMILY_LEISURE = "family_leisure"
    WELLNESS_SEEKER = "wellness_seeker"
    CULTURE_EXPLORER = "culture_explorer"
    GENERAL_LEISURE = "general_leisure"


class StayStage(StrEnum):
    PRE_STAY = "pre_stay"
    IN_HOUSE = "in_house"
    POST_STAY = "post_stay"
    NON_RESIDENT = "non_resident"


class VIPTier(StrEnum):
    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"
    SINA_PRIVILEGE_VIP = "sina_privilege_vip"


class ConciergeCategory(StrEnum):
    DINING = "dining"
    SPA_WELLNESS = "spa_wellness"
    TRANSPORT = "transport"
    CITY_EXPERIENCE = "city_experience"
    ROOM_AMENITY = "room_amenity"
    FEEDBACK = "feedback"
    SPECIAL_OCCASION = "special_occasion"


class GuestPreferences(BaseModel):
    dietary_restrictions: list[str] = Field(
        default_factory=list,
        description="e.g. ['celiachia / senza glutine', 'vegetariano']",
    )
    room_preferences: list[str] = Field(
        default_factory=list,
        description="e.g. ['piano alto', 'cuscini anallergici', 'vista panoramica']",
    )
    favorite_drinks: list[str] = Field(
        default_factory=list,
        description="e.g. ['Franciacorta', 'espresso doppio']",
    )
    special_notes: str | None = Field(
        default=None,
        description="Concierge internal behavioral notes or special habits",
    )


class GuestProfile(BaseModel):
    id: str
    phone_number: str = Field(description="E.164 or normalized phone number")
    email: str | None = None
    title: str | None = Field(
        default=None,
        description="Honorific title: 'Signor', 'Signora', or None",
    )
    first_name: str
    last_name: str
    preferred_language: str = "it"
    vip_tier: VIPTier = VIPTier.STANDARD
    persona: TravelPersona = TravelPersona.GENERAL_LEISURE
    preferences: GuestPreferences = Field(default_factory=GuestPreferences)
    total_stays: int = 1
    loyalty_points: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class HotelProperty(BaseModel):
    id: str
    name: str
    city: str
    address: str
    phone_number: str
    amenities: list[str] = Field(default_factory=list)
    schedules: dict[str, str] = Field(
        default_factory=dict,
        description="Service schedules, e.g. {'colazione': '07:00 - 10:30'}",
    )


class HotelStay(BaseModel):
    id: str
    guest_id: str
    hotel_id: str
    room_number: str | None = None
    room_type: str
    check_in_date: date
    check_out_date: date
    stage: StayStage
    party_size: int = 2
    special_occasion: str | None = Field(
        default=None,
        description="e.g. '10° Anniversario di Nozze', 'Conferenza Finanziaria'",
    )
    internal_notes: str | None = None


class ConciergeRequest(BaseModel):
    id: str
    stay_id: str | None = None
    guest_id: str
    category: ConciergeCategory
    title: str
    request_details: str
    status: str = "confirmed"
    scheduled_time: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class CityRecommendationItem(BaseModel):
    id: str
    hotel_id: str
    category: ConciergeCategory
    title: str
    description_it: str
    description_en: str
    tags: list[str] = Field(default_factory=list)
    recommended_for: list[TravelPersona] = Field(default_factory=list)
    insider_tip_it: str | None = None


class GuestFeedback(BaseModel):
    id: str
    guest_id: str
    stay_id: str | None = None
    nps_score: int = Field(ge=1, le=10)
    comments: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class CallerCRMContext(BaseModel):
    is_known_guest: bool
    guest: GuestProfile | None = None
    stay: HotelStay | None = None
    property: HotelProperty | None = None
    stage: StayStage = StayStage.NON_RESIDENT
    suggested_greeting_it: str
