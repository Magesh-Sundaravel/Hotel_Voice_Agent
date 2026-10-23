import asyncio
import logging
from collections.abc import AsyncGenerator

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsTTSService:
    """Streams 8kHz mu-law audio directly from ElevenLabs for Twilio Media Streams."""

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str | None = None,
    ):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.voice_id = voice_id or settings.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
        self.model_id = model_id or settings.ELEVENLABS_MODEL_ID or "eleven_turbo_v2_5"

    async def stream_speech(
        self,
        text: str,
        chunk_size: int = 320,  # 320 bytes = 40ms at 8kHz 8-bit mulaw
    ) -> AsyncGenerator[bytes, None]:
        """Streams raw 8kHz mu-law bytes for the given Italian text.

        If api_key is missing, yields mock silence/tones to keep the pipeline alive.
        """
        if not text or not text.strip():
            return

        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY is not configured; generating mock audio.")
            # Generate 1 second of mock mu-law silence (0xFF in mu-law is quiet)
            mock_bytes = b"\xff" * 8000
            for i in range(0, len(mock_bytes), chunk_size):
                yield mock_bytes[i : i + chunk_size]
                await asyncio.sleep(0.04)  # real-time pacing 40ms
            return

        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
            f"?output_format=ulaw_8000"
        )
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/basic",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
            },
        }

        try:
            async with (
                httpx.AsyncClient(timeout=30.0) as client,
                client.stream("POST", url, headers=headers, json=payload) as response,
            ):
                if response.status_code != 200:
                    err_body = await response.aread()
                    logger.error(
                        "ElevenLabs TTS failed: status %s, error: %s",
                        response.status_code,
                        err_body.decode(errors="replace"),
                    )
                    return

                buffer = bytearray()
                async for chunk in response.aiter_bytes():
                    buffer.extend(chunk)
                    while len(buffer) >= chunk_size:
                        send_chunk = bytes(buffer[:chunk_size])
                        del buffer[:chunk_size]
                        yield send_chunk

                if buffer:
                    yield bytes(buffer)

        except (httpx.HTTPError, OSError, ValueError) as e:
            logger.error("Exception during ElevenLabs TTS streaming: %s", e)
