import json

from src.tools.base import BaseTool
from pydantic import BaseModel, Field

from src.models import ConciergeCategory
from src.services.guest_crm_service import GuestCRMService


class LookupCallerInput(BaseModel):
    phone_number: str = Field(
        description="Numero di telefono del chiamante (es. '+39 333 1112233')"
    )


class LookupCallerCRMTool(BaseTool):
    name: str = "lookup_caller_crm"
    description: str = (
        "Cerca il profilo dell'ospite e lo stato del soggiorno nel CRM di Sina Hotels. "
        "Restituisce se l'ospite è riconosciuto, il livello VIP, la camera se in-house, "
        "le preferenze note (es. celiachia, cuscini, bevande) e il saluto suggerito."
    )
    args_schema: type[BaseModel] = LookupCallerInput
    crm_service: GuestCRMService

    async def _arun(self, phone_number: str) -> str:
        ctx = await self.crm_service.lookup_caller_context(phone_number)
        if not ctx.is_known_guest or not ctx.guest:
            return json.dumps(
                {
                    "is_known_guest": False,
                    "stage": ctx.stage.value,
                    "suggested_greeting_it": ctx.suggested_greeting_it,
                    "notes": "Ospite non registrato o prima chiamata da questo numero.",
                },
                ensure_ascii=False,
            )

        guest = ctx.guest
        stay = ctx.stay
        return json.dumps(
            {
                "is_known_guest": True,
                "first_name": guest.first_name,
                "last_name": guest.last_name,
                "vip_tier": guest.vip_tier.value,
                "persona": guest.persona.value,
                "stage": ctx.stage.value,
                "hotel": ctx.property.name if ctx.property else "Sina Bernini Bristol",
                "room_number": stay.room_number if stay else None,
                "room_type": stay.room_type if stay else None,
                "special_occasion": stay.special_occasion if stay else None,
                "dietary_restrictions": guest.preferences.dietary_restrictions,
                "room_preferences": guest.preferences.room_preferences,
                "favorite_drinks": guest.preferences.favorite_drinks,
                "concierge_notes": guest.preferences.special_notes,
                "suggested_greeting_it": ctx.suggested_greeting_it,
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class RecordGuestPreferenceInput(BaseModel):
    phone_number: str = Field(description="Numero di telefono dell'ospite")
    dietary_restriction: str | None = Field(
        default=None,
        description="Allergie o intolleranze alimentari (es. 'celiachia', 'senza glutine', 'vegetariano')",
    )
    room_preference: str | None = Field(
        default=None,
        description="Preferenze per la camera (es. 'piano alto', 'cuscini anallergici', 'silenzioso')",
    )
    favorite_drink: str | None = Field(
        default=None,
        description="Bevanda o cocktail preferito (es. 'Franciacorta', 'caffè espresso doppio')",
    )
    special_note: str | None = Field(
        default=None,
        description="Note comportamentali o richieste per lo staff (es. 'Festeggiano anniversario')",
    )


class RecordGuestPreferenceTool(BaseTool):
    name: str = "record_guest_preference"
    description: str = (
        "Registra o aggiorna nel CRM di Sina Hotels le preferenze o restrizioni dell'ospite. "
        "Se viene aggiunta un'allergia o nota speciale, genera un'allerta immediata per il personale."
    )
    args_schema: type[BaseModel] = RecordGuestPreferenceInput
    crm_service: GuestCRMService

    async def _arun(
        self,
        phone_number: str,
        dietary_restriction: str | None = None,
        room_preference: str | None = None,
        favorite_drink: str | None = None,
        special_note: str | None = None,
    ) -> str:
        guest = await self.crm_service.save_guest_preference(
            phone=phone_number,
            dietary_restriction=dietary_restriction,
            room_preference=room_preference,
            favorite_drink=favorite_drink,
            special_note=special_note,
        )
        return json.dumps(
            {
                "success": True,
                "message_it": f"Preferenze aggiornate con successo per {guest.full_name}.",
                "current_dietary": guest.preferences.dietary_restrictions,
                "current_room_preferences": guest.preferences.room_preferences,
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class RequestConciergeServiceInput(BaseModel):
    phone_number: str = Field(description="Numero di telefono dell'ospite")
    category: str = Field(
        description="Categoria: 'dining', 'spa_wellness', 'transport', 'city_experience', 'room_amenity'"
    )
    title: str = Field(
        description="Titolo sintetico della richiesta (es. 'Transfer NCC Fiumicino', 'Tavolo Terrazza The Flair')"
    )
    details: str = Field(
        description="Dettagli specifici (numero persone, orario, volo, preferenze tavolo)"
    )
    scheduled_time: str | None = Field(
        default=None,
        description="Orario o data programmata (es. '20:30' o '14:15')",
    )


class RequestConciergeServiceTool(BaseTool):
    name: str = "request_concierge_service"
    description: str = (
        "Inoltra una richiesta di servizio concierge (transfer privato, prenotazione spa, "
        "tavolo ristorante, tour culturale, amenità in camera) registrandola nel CRM e notificando lo staff."
    )
    args_schema: type[BaseModel] = RequestConciergeServiceInput
    crm_service: GuestCRMService

    async def _arun(
        self,
        phone_number: str,
        category: str,
        title: str,
        details: str,
        scheduled_time: str | None = None,
    ) -> str:
        try:
            cat_enum = ConciergeCategory(category.lower())
        except ValueError:
            cat_enum = ConciergeCategory.CITY_EXPERIENCE

        req = await self.crm_service.create_concierge_request(
            phone=phone_number,
            category=cat_enum,
            title=title,
            details=details,
            scheduled_time=scheduled_time,
        )
        return json.dumps(
            {
                "success": True,
                "request_id": req.id,
                "title": req.title,
                "message_it": f"Richiesta '{req.title}' registrata con successo. Il Concierge Sina ne ha preso carico.",
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class GetCityRecommendationsInput(BaseModel):
    phone_number: str = Field(description="Numero di telefono dell'ospite")
    category: str | None = Field(
        default=None,
        description="Filtro opzionale: 'dining', 'spa_wellness', 'transport', 'city_experience'",
    )


class GetCityRecommendationsTool(BaseTool):
    name: str = "get_city_recommendations"
    description: str = (
        "Fornisce consigli ed esperienze esclusive curate dal Concierge Sina (ristoranti rooftop, "
        "musei e mostre, transfer, spa, tour romantici o per famiglie) personalizzate per il profilo dell'ospite."
    )
    args_schema: type[BaseModel] = GetCityRecommendationsInput
    crm_service: GuestCRMService

    async def _arun(
        self,
        phone_number: str,
        category: str | None = None,
    ) -> str:
        cat_enum = None
        if category:
            try:
                cat_enum = ConciergeCategory(category.lower())
            except ValueError:
                pass

        recs = await self.crm_service.get_personalized_recommendations(
            phone=phone_number,
            category=cat_enum,
        )
        results = [
            {
                "title": r.title,
                "category": r.category.value,
                "description_it": r.description_it,
                "insider_tip_it": r.insider_tip_it,
                "tags": r.tags,
            }
            for r in recs[:4]
        ]
        return json.dumps({"recommendations": results}, ensure_ascii=False)

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class SubmitGuestFeedbackInput(BaseModel):
    phone_number: str = Field(description="Numero di telefono dell'ospite")
    nps_score: int = Field(
        description="Punteggio da 1 a 10 sull'esperienza del soggiorno o servizio"
    )
    comments: str | None = Field(
        default=None, description="Commenti o suggerimenti espressi dall'ospite"
    )


class SubmitGuestFeedbackTool(BaseTool):
    name: str = "submit_guest_feedback"
    description: str = (
        "Registra il feedback o punteggio NPS (1-10) rilasciato dall'ospite al termine del soggiorno "
        "o dopo un'esperienza, aggiornando il profilo e notificando la direzione."
    )
    args_schema: type[BaseModel] = SubmitGuestFeedbackInput
    crm_service: GuestCRMService

    async def _arun(
        self,
        phone_number: str,
        nps_score: int,
        comments: str | None = None,
    ) -> str:
        fb = await self.crm_service.record_feedback(
            phone=phone_number,
            nps_score=nps_score,
            comments=comments,
        )
        return json.dumps(
            {
                "success": True,
                "feedback_id": fb.id,
                "message_it": "Grazie di cuore per aver condiviso la Sua opinione. Il Suo riscontro è prezioso per Sina Hotels.",
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


def build_crm_tools(crm_service: GuestCRMService) -> list[BaseTool]:
    return [
        LookupCallerCRMTool(crm_service=crm_service),
        RecordGuestPreferenceTool(crm_service=crm_service),
        RequestConciergeServiceTool(crm_service=crm_service),
        GetCityRecommendationsTool(crm_service=crm_service),
        SubmitGuestFeedbackTool(crm_service=crm_service),
    ]
