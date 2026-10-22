from src.models import RestaurantSettings
from src.repositories.base import BaseRestaurantRepository


class RestaurantService:
    def __init__(self, restaurant_repo: BaseRestaurantRepository):
        self.restaurant_repo = restaurant_repo

    async def get_settings(self, restaurant_id: str) -> RestaurantSettings | None:
        return await self.restaurant_repo.get_settings(restaurant_id)

    async def get_opening_hours_text(self, restaurant_id: str) -> str:
        settings = await self.restaurant_repo.get_settings(restaurant_id)
        if not settings:
            return "Informazioni sugli orari non disponibili al momento."
        shift_lines = [
            f"- {s.name_it.capitalize()}: dalle {s.start_time} alle {s.end_time} (ultimo ingresso alle {s.last_seating_time})"
            for s in settings.shifts
        ]
        return f"Gli orari di apertura di {settings.name} sono:\n" + "\n".join(
            shift_lines
        )

    async def answer_faq(self, restaurant_id: str, query: str) -> str | None:
        faqs = await self.restaurant_repo.get_faqs(restaurant_id)
        query_lower = query.lower()

        # Keyword matching
        best_match = None
        max_matches = 0

        for faq in faqs:
            matches = sum(1 for kw in faq.keywords if kw.lower() in query_lower)
            if faq.category.lower() in query_lower:
                matches += 2
            if matches > max_matches:
                max_matches = matches
                best_match = faq

        if best_match and max_matches > 0:
            return best_match.answer_it

        return None
