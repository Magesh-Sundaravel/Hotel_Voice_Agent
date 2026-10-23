from src.agent.prompts import _build_room_rates_section, get_hotel_system_prompt
from src.models.hotel_booking import ROOM_CATEGORY_DETAILS, RoomCategory


def test_build_room_rates_section():
    section = _build_room_rates_section()
    assert "HOTEL ROOM INVENTORY & RATES:" in section
    for details in ROOM_CATEGORY_DETAILS.values():
        name = details["name_it"]
        price = int(details["price_per_night"])
        assert name in section
        assert f"€{price}" in section


def test_get_hotel_system_prompt_includes_rates():
    prompt = get_hotel_system_prompt(hotel_name="Sina Bernini Bristol")
    assert "HOTEL ROOM INVENTORY & RATES:" in prompt
    assert "Camera Superior: €250 / notte" in prompt
    assert "Camera Deluxe con Vista Città: €350 / notte" in prompt
    assert "Junior Suite con Balcone: €480 / notte" in prompt
    assert "Suite Panoramica Barberini: €750 / notte" in prompt
    assert "max 4 ospiti, terrazza 360°, idromassaggio" in prompt


def test_prompt_rates_dynamically_change(monkeypatch):
    modified_details = {
        RoomCategory.SUPERIOR: {
            "name_it": "Camera Superior Special",
            "price_per_night": 299.0,
            "max_guests": 2,
            "description_it": "Test desc",
            "features_it": "",
        }
    }
    monkeypatch.setattr("src.agent.prompts.ROOM_CATEGORY_DETAILS", modified_details)
    prompt = get_hotel_system_prompt()
    assert "Camera Superior Special: €299 / notte" in prompt
