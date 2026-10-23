"""Voice Activity Detection (VAD) module for real-time telephony audio.

Supports WebRTC VAD, pure RMS threshold, with fast pre-filtering to minimize CPU usage.
Twilio Media Streams send 8000 Hz, 16-bit linear PCM in 20ms frames (320 bytes per frame).
"""

from __future__ import annotations

import logging
from typing import Literal

from src.config import settings
from src.voice.audio_utils import calculate_rms

logger = logging.getLogger(__name__)

try:
    import webrtcvad

    WEBRTC_AVAILABLE = True
except ImportError:
    webrtcvad = None
    WEBRTC_AVAILABLE = False


class VoiceActivityDetector:
    """Detects human speech in PCM audio frames with configurable providers and pre-filters."""

    def __init__(
        self,
        provider: Literal["webrtc", "rms"] | str | None = None,
        mode: int | None = None,
        rms_prefilter_threshold: float | None = None,
        sample_rate: int = 8000,
    ) -> None:
        self.provider = (provider or getattr(settings, "VAD_PROVIDER", "webrtc")).lower()
        self.mode = mode if mode is not None else getattr(settings, "VAD_MODE", 2)
        self.rms_prefilter_threshold = (
            rms_prefilter_threshold
            if rms_prefilter_threshold is not None
            else getattr(settings, "VAD_RMS_PREFILTER_THRESHOLD", 250.0)
        )
        self.sample_rate = sample_rate

        self._webrtc_vad = None
        if self.provider == "webrtc":
            if WEBRTC_AVAILABLE:
                self._webrtc_vad = webrtcvad.Vad(max(0, min(3, self.mode)))
            else:
                logger.warning("webrtcvad is not installed. Falling back to RMS threshold VAD.")
                self.provider = "rms"

    def is_speech(self, pcm_bytes: bytes) -> bool:
        """Determines whether the given 16-bit linear PCM chunk contains human speech.

        Uses RMS energy as a fast pre-filter: if RMS is below threshold, skips VAD model.
        """
        if not pcm_bytes:
            return False

        # Fast pre-filter: if ambient sound volume is too low, it's silence
        rms = calculate_rms(pcm_bytes)
        if rms < self.rms_prefilter_threshold:
            return False

        # If RMS provider or WebRTC not available, threshold check above is sufficient
        if self.provider != "webrtc" or self._webrtc_vad is None:
            # For pure RMS, use higher threshold (e.g. 700.0)
            return rms >= max(self.rms_prefilter_threshold, 600.0)

        # WebRTC VAD requires frame size of exactly 10, 20, or 30 ms.
        # At 8000 Hz, 16-bit:
        # 10ms = 80 samples * 2 bytes = 160 bytes
        # 20ms = 160 samples * 2 bytes = 320 bytes
        # 30ms = 240 samples * 2 bytes = 480 bytes
        # Twilio sends 20ms chunks (320 bytes PCM).
        frame_size = int(self.sample_rate * 0.02 * 2)  # 320 bytes for 20ms at 8kHz

        if len(pcm_bytes) == frame_size:
            try:
                return self._webrtc_vad.is_speech(pcm_bytes, self.sample_rate)
            except Exception as e:
                logger.debug("webrtcvad check failed: %s, fallback to RMS", e)
                return rms >= 600.0

        # Handle arbitrary chunk lengths by checking full 20ms frames inside the chunk
        offset = 0
        speech_detected = False
        while offset + frame_size <= len(pcm_bytes):
            sub_frame = pcm_bytes[offset : offset + frame_size]
            try:
                if self._webrtc_vad.is_speech(sub_frame, self.sample_rate):
                    speech_detected = True
                    break
            except Exception:
                pass
            offset += frame_size

        return speech_detected or (rms >= 750.0 and len(pcm_bytes) < frame_size)
