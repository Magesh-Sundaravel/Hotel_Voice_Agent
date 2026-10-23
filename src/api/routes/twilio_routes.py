import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket
from pydantic import BaseModel, Field

from src.api.middleware.auth import verify_api_key, verify_twilio_signature
from src.config import settings
from src.integrations.twilio_service import TwilioService
from src.voice.agent import VoiceAgent
from src.voice.pipeline import TwilioMediaStreamPipeline
from src.voice.stt import SpeechToTextService
from src.voice.tts import ElevenLabsTTSService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twilio", tags=["Twilio Voice Integration"])
twilio_service = TwilioService()


@router.post("/incoming-call", dependencies=[Depends(verify_twilio_signature)])
async def handle_incoming_call(request: Request):
    """Twilio Inbound Voice Webhook: returns TwiML to start bi-directional media stream."""
    form_data = await request.form()
    caller_phone = form_data.get("From", "+39 000 0000000")
    call_sid = form_data.get("CallSid", "unknown_call")

    logger.info("Incoming Twilio call from %s (CallSid: %s)", caller_phone, call_sid)

    # Determine websocket URL
    if settings.PUBLIC_URL:
        base = settings.PUBLIC_URL.strip().rstrip("/")
        ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
        stream_url = f"{ws_base}/api/twilio/stream"
    else:
        host = request.headers.get("host", f"localhost:{settings.PORT}")
        scheme = "wss" if request.url.scheme == "https" else "ws"
        stream_url = f"{scheme}://{host}/api/twilio/stream"

    twiml_xml = twilio_service.generate_media_stream_twiml(
        stream_url=stream_url,
        caller_phone=caller_phone,
        hotel_name=settings.DEFAULT_HOTEL_NAME,
    )
    return Response(content=twiml_xml, media_type="application/xml")


@router.websocket("/stream")
async def twilio_audio_stream(websocket: WebSocket):
    """Full-duplex WebSocket stream connecting Twilio audio packets with ElevenLabs and VoiceAgent."""
    await websocket.accept()
    logger.info("Twilio WebSocket connection accepted.")

    # Obtain cached VoiceAgent from app state or create fallback
    agent = getattr(getattr(websocket.app, "state", None), "voice_agent", None)
    if agent is None:
        agent = getattr(getattr(websocket.app, "state", None), "agent_graph", None)
    if agent is None:
        agent = VoiceAgent(
            hotel_id="sina_bernini_bristol",
            hotel_name=settings.DEFAULT_HOTEL_NAME,
            hotel_booking_service=getattr(
                getattr(websocket.app, "state", None), "hotel_booking_service", None
            ),
            guest_crm_service=getattr(getattr(websocket.app, "state", None), "crm_service", None),
        )

    pipeline = TwilioMediaStreamPipeline(
        websocket=websocket,
        voice_agent=agent,
        stt_service=SpeechToTextService(),
        tts_service=ElevenLabsTTSService(),
        hotel_id="sina_bernini_bristol",
        hotel_name=settings.DEFAULT_HOTEL_NAME,
    )

    await pipeline.run()


class OutboundCallRequest(BaseModel):
    to_phone: str = Field(description="Destination phone number, e.g. +393331234567")
    callback_url: str | None = Field(
        default=None,
        description="Optional custom callback TwiML webhook URL. Defaults to {PUBLIC_URL}/api/twilio/incoming-call",
    )


@router.post("/call", dependencies=[Depends(verify_api_key)])
async def trigger_outbound_call(payload: OutboundCallRequest):
    """Triggers an outbound voice call to the guest via Twilio."""
    try:
        call_sid = twilio_service.initiate_outbound_call(
            to_phone=payload.to_phone,
            callback_url=payload.callback_url,
        )
        return {"status": "initiated", "call_sid": call_sid, "to": payload.to_phone}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (RuntimeError, OSError) as e:
        logger.error("Outbound call error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/status", dependencies=[Depends(verify_twilio_signature)])
async def handle_call_status(request: Request):
    """Handles Twilio Call Status events (completed, no-answer, failed)."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    duration = form_data.get("CallDuration")
    logger.info(
        "Twilio Call status: sid=%s, status=%s, duration=%s", call_sid, call_status, duration
    )
    return {"status": "received"}
