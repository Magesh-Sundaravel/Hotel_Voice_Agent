"""Full-duplex streaming audio pipeline between Twilio Media Streams, ElevenLabs, and native VoiceAgent.

Processes 8kHz mu-law audio, handles Voice Activity Detection (VAD), instant barge-in,
and calls the single-loop VoiceAgent without LangGraph.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Any

from fastapi import WebSocket

from src.voice.agent import VoiceAgent
from src.voice.audio_utils import calculate_rms, mulaw_to_pcm
from src.voice.session import CallSession
from src.voice.stt import SpeechToTextService
from src.voice.tts import ElevenLabsTTSService

logger = logging.getLogger(__name__)


class TwilioMediaStreamPipeline:
    """Manages full-duplex streaming audio between Twilio Media Streams, ElevenLabs, and native VoiceAgent."""

    def __init__(
        self,
        websocket: WebSocket,
        voice_agent: VoiceAgent | None = None,
        agent_graph: Any = None,  # Backward compatibility parameter
        stt_service: SpeechToTextService | None = None,
        tts_service: ElevenLabsTTSService | None = None,
        hotel_id: str = "sina_bernini_bristol",
        hotel_name: str = "Sina Bernini Bristol",
        rms_threshold: float = 700.0,
        silence_timeout_sec: float = 0.85,
    ) -> None:
        self.ws = websocket
        self.voice_agent = voice_agent or agent_graph
        self.stt = stt_service or SpeechToTextService()
        self.tts = tts_service or ElevenLabsTTSService()
        self.hotel_id = hotel_id
        self.hotel_name = hotel_name
        self.rms_threshold = rms_threshold
        self.silence_timeout_sec = silence_timeout_sec

        self.stream_sid: str | None = None
        self.call_sid: str | None = None
        self.caller_phone: str = "+39 000 0000000"
        self.session: CallSession | None = None

        # State tracking
        self.inbound_audio_buffer = bytearray()
        self.is_caller_speaking = False
        self.last_speech_time = 0.0
        self.is_bot_speaking = False
        self.current_tts_task: asyncio.Task | None = None
        self.silence_monitor_task: asyncio.Task | None = None
        self.running = True

    async def run(self) -> None:
        """Main execution loop listening to Twilio WebSocket messages."""
        self.silence_monitor_task = asyncio.create_task(self._monitor_silence())

        try:
            while self.running:
                data = await self.ws.receive_text()
                message = json.loads(data)
                event = message.get("event")

                if event == "connected":
                    logger.info("Twilio WebSocket connected.")

                elif event == "start":
                    start_data = message.get("start", {})
                    self.stream_sid = start_data.get("streamSid")
                    self.call_sid = start_data.get("callSid") or "call_unknown"
                    custom_params = start_data.get("customParameters", {})
                    self.caller_phone = (
                        custom_params.get("caller_phone")
                        or custom_params.get("From")
                        or self.caller_phone
                    )
                    self.hotel_name = custom_params.get("hotel_name", self.hotel_name)

                    logger.info(
                        "Twilio Stream started: streamSid=%s, callSid=%s, caller=%s",
                        self.stream_sid,
                        self.call_sid,
                        self.caller_phone,
                    )

                    # Initialize native agent if not pre-provided
                    if self.voice_agent is None:
                        self.voice_agent = VoiceAgent(
                            hotel_id=self.hotel_id,
                            hotel_name=self.hotel_name,
                        )

                    clean_phone = self.caller_phone.replace(" ", "").replace("+", "")
                    self.session = CallSession(
                        call_id=self.call_sid,
                        user_id=f"user_{clean_phone}",
                        caller_phone=self.caller_phone,
                        hotel_id=self.hotel_id,
                        hotel_name=self.hotel_name,
                    )

                    # Send initial warm welcome greeting
                    greeting = (
                        "Buongiorno, sono l'assistente virtuale di Sina Bernini Bristol. "
                        "Come posso aiutarLa oggi?"
                    )
                    self._start_tts_task(greeting)

                elif event == "media":
                    payload_b64 = message.get("media", {}).get("payload")
                    if payload_b64:
                        chunk_mulaw = base64.b64decode(payload_b64)
                        await self._process_inbound_chunk(chunk_mulaw)

                elif event == "stop":
                    logger.info("Twilio Stream stopped: callSid=%s", self.call_sid)
                    self.running = False
                    break

        except (OSError, asyncio.CancelledError, RuntimeError) as e:
            logger.info("Twilio WebSocket closed/exception: %s", e)
        finally:
            self.running = False
            if self.current_tts_task and not self.current_tts_task.done():
                self.current_tts_task.cancel()
            if self.silence_monitor_task and not self.silence_monitor_task.done():
                self.silence_monitor_task.cancel()

    async def _process_inbound_chunk(self, chunk_mulaw: bytes) -> None:
        """Processes 20ms audio chunks from Twilio: VAD, barge-in, buffering."""
        pcm = mulaw_to_pcm(chunk_mulaw)
        rms = calculate_rms(pcm)
        now = time.time()

        if rms > self.rms_threshold:
            # Caller is speaking
            self.last_speech_time = now

            if not self.is_caller_speaking:
                self.is_caller_speaking = True
                logger.debug("Speech started (RMS=%.1f)", rms)

            # BARGE-IN: If bot is currently speaking and user interrupts, cancel playback immediately!
            if self.is_bot_speaking:
                logger.info("Barge-in detected! Silencing bot audio stream.")
                await self._clear_twilio_buffer()
                if self.current_tts_task and not self.current_tts_task.done():
                    self.current_tts_task.cancel()
                self.is_bot_speaking = False

            self.inbound_audio_buffer.extend(chunk_mulaw)
        else:
            # Silence / ambient background
            if self.is_caller_speaking:
                self.inbound_audio_buffer.extend(chunk_mulaw)

    async def _monitor_silence(self) -> None:
        """Polls every 50ms to detect end of caller turn when silence follows speech."""
        while self.running:
            await asyncio.sleep(0.05)
            if not self.is_caller_speaking or not self.inbound_audio_buffer:
                continue

            elapsed_silence = time.time() - self.last_speech_time
            if elapsed_silence >= self.silence_timeout_sec:
                # Caller finished speaking
                self.is_caller_speaking = False
                audio_to_transcribe = bytes(self.inbound_audio_buffer)
                self.inbound_audio_buffer.clear()

                # Process the audio in the background
                asyncio.create_task(self._handle_user_turn(audio_to_transcribe))

    async def _handle_user_turn(self, audio_mulaw: bytes) -> None:
        """Transcribes caller speech, invokes native VoiceAgent turn, and speaks response."""
        transcript = await self.stt.transcribe_mulaw(audio_mulaw)
        if not transcript or not transcript.strip():
            logger.debug("Empty or unintelligible audio turn, ignoring.")
            return

        logger.info("Caller said: '%s'", transcript)

        if not self.session:
            clean_phone = self.caller_phone.replace(" ", "").replace("+", "")
            self.session = CallSession(
                call_id=self.call_sid or "call_unknown",
                user_id=f"user_{clean_phone}",
                caller_phone=self.caller_phone,
                hotel_id=self.hotel_id,
                hotel_name=self.hotel_name,
            )

        try:
            if hasattr(self.voice_agent, "run_turn"):
                turn_result = await self.voice_agent.run_turn(self.session, transcript)
                reply_text = turn_result.reply_text
                call_ended = turn_result.call_ended
            else:
                # Fallback for legacy interface
                reply_text = "Certamente."
                call_ended = False

            logger.info("Agent replying: '%s'", reply_text)
            self._start_tts_task(reply_text)

            if call_ended:
                logger.info("Call ended by agent tool. Scheduling disconnect.")
                asyncio.create_task(self._disconnect_after_delay(3.0))

        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Error executing agent turn: %s", e)
            error_reply = "Mi scusi, si è verificato un errore momentaneo. Può ripetere?"
            self._start_tts_task(error_reply)

    async def _disconnect_after_delay(self, delay: float) -> None:
        """Gracefully terminates stream after farewell speech."""
        await asyncio.sleep(delay)
        self.running = False
        try:
            await self.ws.close()
        except Exception as e:  # noqa: BLE001
            logger.debug("Error closing websocket on disconnect: %s", e)

    def _start_tts_task(self, text: str) -> None:
        """Spawns an async task to stream TTS audio to Twilio."""
        if self.current_tts_task and not self.current_tts_task.done():
            self.current_tts_task.cancel()
        self.current_tts_task = asyncio.create_task(self._stream_tts_to_twilio(text))

    async def _stream_tts_to_twilio(self, text: str) -> None:
        """Streams 8kHz mu-law audio chunks from ElevenLabs into the Twilio WebSocket."""
        if not self.stream_sid:
            return

        self.is_bot_speaking = True
        try:
            async for chunk in self.tts.stream_speech(text):
                if not self.running or not self.is_bot_speaking:
                    break

                payload = base64.b64encode(chunk).decode("ascii")
                msg = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload},
                }
                await self.ws.send_text(json.dumps(msg))
                await asyncio.sleep(0.035)

        except asyncio.CancelledError:
            logger.debug("TTS playback task cancelled (barge-in or new turn).")
        except (OSError, RuntimeError) as e:
            logger.error("Error streaming TTS audio to Twilio: %s", e)
        finally:
            self.is_bot_speaking = False

    async def _clear_twilio_buffer(self) -> None:
        """Sends 'clear' event to Twilio to dump pending unplayed audio (instant barge-in)."""
        if not self.stream_sid:
            return
        msg = {
            "event": "clear",
            "streamSid": self.stream_sid,
        }
        try:
            await self.ws.send_text(json.dumps(msg))
        except (OSError, RuntimeError) as e:
            logger.debug("Could not send clear event: %s", e)
