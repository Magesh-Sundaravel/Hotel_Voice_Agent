from enum import Enum

from pydantic import BaseModel, Field


class ShiftName(str, Enum):
    LUNCH = "lunch"
    DINNER = "dinner"


class Shift(BaseModel):
    name: ShiftName
    name_it: str = Field(description="Italian name: pranzo o cena")
    start_time: str = Field(description="HH:MM format, e.g. 12:30")
    end_time: str = Field(description="HH:MM format, e.g. 14:30")
    last_seating_time: str = Field(description="HH:MM format, e.g. 14:00")


class Table(BaseModel):
    id: str
    restaurant_id: str
    table_number: int
    min_capacity: int = 1
    max_capacity: int = 4
    is_active: bool = True


class FAQItem(BaseModel):
    id: str
    category: str
    question_it: str
    answer_it: str
    keywords: list[str] = Field(default_factory=list)


class RestaurantSettings(BaseModel):
    id: str
    name: str
    phone_number: str
    address: str
    timezone: str = "Europe/Rome"
    slot_duration_minutes: int = 90
    max_party_size: int = 10
    shifts: list[Shift] = Field(default_factory=list)
    faqs: list[FAQItem] = Field(default_factory=list)
