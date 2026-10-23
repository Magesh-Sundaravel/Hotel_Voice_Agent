import logging

import httpx

from src.config import settings
from src.voice.audio_utils import mulaw_to_wav_bytes

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """Transcribes audio using ElevenLabs Scribe or Groq Whisper with Italian language models."""

    def __init__(
        self,
        elevenlabs_api_key: str | None = None,
        groq_api_key: str | None = None,
        provider: str | None = None,
    ):
        self.elevenlabs_api_key = elevenlabs_api_key or settings.ELEVENLABS_API_KEY
        self.groq_api_key = groq_api_key or settings.GROQ_API_KEY
        self.provider = (provider or settings.STT_PROVIDER).lower()

    async def transcribe_mulaw(self, mulaw_bytes: bytes) -> str:
        """Converts raw 8kHz mu-law audio bytes from Twilio to WAV and transcribes."""
        if not mulaw_bytes or len(mulaw_bytes) < 400:  # less than 50ms of audio
            return ""

        wav_bytes = mulaw_to_wav_bytes(mulaw_bytes, sample_rate=8000)
        return await self.transcribe_wav(wav_bytes)

    async def transcribe_wav(self, wav_bytes: bytes) -> str:
        """Transcribes WAV audio using the configured provider."""
        # Check ElevenLabs first if selected and key available
        if self.provider == "elevenlabs" and self.elevenlabs_api_key:
            transcript = await self._transcribe_elevenlabs(wav_bytes)
            if transcript:
                return transcript

        # Check Groq Whisper (ultra-fast ~150ms transcription in Italian)
        if self.groq_api_key:
            transcript = await self._transcribe_groq(wav_bytes)
            if transcript:
                return transcript

        # Fallback to ElevenLabs if Groq wasn't primary but key exists
        if self.elevenlabs_api_key:
            return await self._transcribe_elevenlabs(wav_bytes)

        logger.warning("No STT API key configured (neither ElevenLabs nor Groq).")
        return ""

    async def _transcribe_elevenlabs(self, wav_bytes: bytes) -> str:
        """Calls ElevenLabs speech-to-text API."""
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": self.elevenlabs_api_key}
        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav"),
        }
        data = {
            "model_id": "scribe_v1",
            "language_code": "it",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    data = res.json()
                    text = data.get("text", "").strip()
                    logger.info("ElevenLabs STT transcript: %s", text)
                    return text
                else:
                    logger.warning("ElevenLabs STT error: %s - %s", res.status_code, res.text)
        except (httpx.HTTPError, OSError, ValueError) as e:
            logger.error("ElevenLabs STT exception: %s", e)
        return ""

    async def _transcribe_groq(self, wav_bytes: bytes) -> str:
        """Calls Groq Whisper audio transcriptions API."""
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}
        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav"),
        }
        data = {
            "model": "whisper-large-v3-turbo",
            "language": "it",
            "response_format": "json",
            "temperature": "0.0",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    text = res.json().get("text", "").strip()
                    logger.info("Groq Whisper transcript: %s", text)
                    return text
                else:
                    logger.warning("Groq STT error: %s - %s", res.status_code, res.text)
        except (httpx.HTTPError, OSError, ValueError) as e:
            logger.error("Groq STT exception: %s", e)
        return ""
