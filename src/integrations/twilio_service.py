import logging

from twilio.rest import Client
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse

from src.config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    """Handles Twilio TwiML generation and outbound SMS notifications."""

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        phone_number: str | None = None,
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.phone_number = phone_number or settings.TWILIO_PHONE_NUMBER
        self._client: Client | None = None

        if self.account_sid and self.auth_token:
            try:
                self._client = Client(self.account_sid, self.auth_token)
            except (ValueError, RuntimeError) as e:
                logger.warning("Could not initialize Twilio client: %s", e)

    def generate_media_stream_twiml(
        self,
        stream_url: str,
        caller_phone: str | None = None,
        hotel_name: str | None = None,
    ) -> str:
        """Builds TwiML instructions telling Twilio to connect the call to our WebSocket."""
        response = VoiceResponse()
        connect = Connect()
        stream = Stream(url=stream_url)

        if caller_phone:
            stream.parameter(name="caller_phone", value=caller_phone)
        if hotel_name:
            stream.parameter(name="hotel_name", value=hotel_name)

        connect.append(stream)
        response.append(connect)
        return str(response)

    async def send_sms(
        self,
        to_phone: str,
        body: str,
    ) -> bool:
        """Sends an outbound SMS message to the given phone number."""
        if not self._client or not self.phone_number:
            logger.info(
                "[SIMULATED SMS] To: %s | From: %s | Message: %s",
                to_phone,
                self.phone_number or "SINA-HOTELS",
                body,
            )
            return True

        try:
            message = self._client.messages.create(
                body=body,
                from_=self.phone_number,
                to=to_phone,
            )
            logger.info("Twilio SMS sent to %s, SID: %s", to_phone, message.sid)
            return True
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to send Twilio SMS to %s: %s", to_phone, e)
            return False

    async def send_booking_confirmation_sms(
        self,
        to_phone: str,
        guest_name: str,
        reference_code: str,
        category: str,
        check_in_date: str,
        check_out_date: str,
    ) -> bool:
        """Sends an SMS confirmation to the guest's mobile phone."""
        body = (
            f"Sina Bernini Bristol: Gentile {guest_name}, Le confermiamo la prenotazione "
            f"{reference_code} per {category} (Arrivo: {check_in_date}, Partenza: {check_out_date}). "
            f"Per assistenza o transfer: +39 06 4883051. A presto a Roma!"
        )
        return await self.send_sms(to_phone=to_phone, body=body)

    def initiate_outbound_call(
        self,
        to_phone: str,
        callback_url: str | None = None,
    ) -> str:
        """Initiates an outbound phone call via Twilio to a given phone number.

        When the call connects, Twilio fetches instructions from callback_url
        (defaulting to {PUBLIC_URL}/api/twilio/incoming-call) to stream the voice conversation.
        """
        if not self._client or not self.phone_number:
            raise ValueError(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) "
                "are required to make outbound calls."
            )

        url = callback_url or (
            f"{settings.PUBLIC_URL.strip().rstrip('/')}/api/twilio/incoming-call"
            if settings.PUBLIC_URL
            else None
        )
        if not url:
            raise ValueError(
                "PUBLIC_URL must be configured to supply Twilio with the voice webhook."
            )

        call = self._client.calls.create(
            to=to_phone,
            from_=self.phone_number,
            url=url,
        )
        logger.info("Twilio outbound call initiated to %s: SID=%s", to_phone, call.sid)
        return call.sid
