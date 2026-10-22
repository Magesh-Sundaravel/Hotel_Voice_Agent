from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationType(str, Enum):
    NEW_BOOKING = "new_booking"
    MODIFICATION = "modification"
    CANCELLATION = "cancellation"
    OWNER_MESSAGE = "owner_message"
    ALLERGY_ALERT = "allergy_alert"
    VIP_ALERT = "vip_alert"
    ANNIVERSARY_ALERT = "anniversary_alert"
    CONCIERGE_REQUEST = "concierge_request"
    GUEST_FEEDBACK = "guest_feedback"
    TRANSFER_REQUEST = "transfer_request"


class CRMNotification(BaseModel):
    id: str
    restaurant_id: str
    type: NotificationType
    title: str
    message: str
    customer_name: str | None = None
    customer_phone: str | None = None
    reference_code: str | None = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=utc_now)
