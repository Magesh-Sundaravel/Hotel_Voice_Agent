import json

from src.tools.base import BaseTool
from pydantic import BaseModel, Field

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService


class SendBookingConfirmationEmailInput(BaseModel):
    guest_email: str = Field(description="Indirizzo email dell'ospite (es. mario.rossi@email.it)")
    guest_name: str = Field(description="Nome e cognome dell'ospite")
    reference_code: str = Field(description="Codice prenotazione (es. SINA-4020)")
    room_category: str = Field(
        description="Tipologia camera prenotata (Superior, Deluxe, Junior Suite, Suite Panoramica)"
    )
    check_in_date: str = Field(description="Data di check-in (YYYY-MM-DD)")
    check_out_date: str = Field(description="Data di check-out (YYYY-MM-DD)")
    guests_count: int = Field(default=2, description="Numero di ospiti")
    total_price: int | None = Field(default=None, description="Prezzo totale in Euro")
    room_number: str | None = Field(default=None, description="Numero camera assegnata")
    special_requests: str | None = Field(default=None, description="Eventuali richieste speciali o note")


class SendBookingConfirmationEmailTool(BaseTool):
    name: str = "send_booking_confirmation_email"
    description: str = (
        "Invia una formale ed elegante email di conferma prenotazione all'indirizzo email fornito dall'ospite, "
        "completa di riepilogo soggiorno, orari di check-in/out e contatti di Sina Bernini Bristol."
    )
    args_schema: type[BaseModel] = SendBookingConfirmationEmailInput
    email_service: EmailService

    async def _arun(
        self,
        guest_email: str,
        guest_name: str,
        reference_code: str,
        room_category: str,
        check_in_date: str,
        check_out_date: str,
        guests_count: int = 2,
        total_price: int | None = None,
        room_number: str | None = None,
        special_requests: str | None = None,
    ) -> str:
        if "@" not in guest_email or "." not in guest_email:
            return json.dumps(
                {
                    "success": False,
                    "message_it": f"L'indirizzo email '{guest_email}' non sembra valido. La prego di verificare.",
                },
                ensure_ascii=False,
            )

        ok = await self.email_service.send_room_booking_confirmation(
            to_email=guest_email.strip(),
            guest_name=guest_name.strip(),
            reference_code=reference_code.strip(),
            room_category=room_category.strip(),
            check_in_date=check_in_date.strip(),
            check_out_date=check_out_date.strip(),
            guests_count=guests_count,
            total_price=total_price,
            room_number=room_number,
            special_requests=special_requests,
        )

        if ok:
            return json.dumps(
                {
                    "success": True,
                    "message_it": f"Email di conferma inviata con successo a {guest_email}.",
                },
                ensure_ascii=False,
            )
        else:
            return json.dumps(
                {
                    "success": False,
                    "message_it": f"Impossibile inviare l'email a {guest_email} in questo momento. Notifica comunque registrata nel sistema.",
                },
                ensure_ascii=False,
            )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class SendBookingConfirmationSmsInput(BaseModel):
    guest_phone: str = Field(description="Numero di cellulare dell'ospite (es. +393331234567)")
    guest_name: str = Field(description="Nome e cognome dell'ospite")
    reference_code: str = Field(description="Codice prenotazione (es. SINA-4020)")
    room_category: str = Field(description="Tipologia camera prenotata")
    check_in_date: str = Field(description="Data di check-in (YYYY-MM-DD)")
    check_out_date: str = Field(description="Data di check-out (YYYY-MM-DD)")


class SendBookingConfirmationSmsTool(BaseTool):
    name: str = "send_booking_confirmation_sms"
    description: str = (
        "Invia un messaggio SMS di conferma prenotazione sul cellulare dell'ospite "
        "con codice di prenotazione, date e contatti del Sina Bernini Bristol."
    )
    args_schema: type[BaseModel] = SendBookingConfirmationSmsInput
    twilio_service: TwilioService

    async def _arun(
        self,
        guest_phone: str,
        guest_name: str,
        reference_code: str,
        room_category: str,
        check_in_date: str,
        check_out_date: str,
    ) -> str:
        ok = await self.twilio_service.send_booking_confirmation_sms(
            to_phone=guest_phone.strip(),
            guest_name=guest_name.strip(),
            reference_code=reference_code.strip(),
            category=room_category.strip(),
            check_in_date=check_in_date.strip(),
            check_out_date=check_out_date.strip(),
        )
        if ok:
            return json.dumps(
                {
                    "success": True,
                    "message_it": f"SMS di conferma inviato al numero {guest_phone}.",
                },
                ensure_ascii=False,
            )
        else:
            return json.dumps(
                {
                    "success": False,
                    "message_it": f"Non è stato possibile recapitare l'SMS al numero {guest_phone}.",
                },
                ensure_ascii=False,
            )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


def build_communication_tools(
    email_service: EmailService | None = None,
    twilio_service: TwilioService | None = None,
) -> list[BaseTool]:
    """Factory creating communication tools for the agent."""
    e_svc = email_service or EmailService()
    t_svc = twilio_service or TwilioService()
    return [
        SendBookingConfirmationEmailTool(email_service=e_svc),
        SendBookingConfirmationSmsTool(twilio_service=t_svc),
    ]
