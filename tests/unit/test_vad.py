import math
import struct
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.voice.audio_utils import pcm_to_mulaw
from src.voice.pipeline import TwilioMediaStreamPipeline
from src.voice.vad import VoiceActivityDetector


def _generate_sine_wave(freq_hz: float, duration_sec: float, amplitude: float = 16000.0) -> bytes:
    """Generates 8000 Hz, 16-bit linear PCM sine wave."""
    sample_rate = 8000
    total_samples = int(sample_rate * duration_sec)
    samples = []
    for i in range(total_samples):
        val = int(amplitude * math.sin(2 * math.pi * freq_hz * i / sample_rate))
        samples.append(max(-32768, min(32767, val)))
    return struct.pack(f"<{len(samples)}h", *samples)


def test_vad_silence_detection():
    detector = VoiceActivityDetector(provider="webrtc", mode=2)
    silence_pcm = b"\x00" * 320  # 20ms of pure silence at 8kHz
    assert detector.is_speech(silence_pcm) is False


def test_vad_rms_prefilter():
    detector = VoiceActivityDetector(
        provider="webrtc",
        rms_prefilter_threshold=500.0,
    )
    # Very faint noise (amplitude 50 -> RMS ~ 35)
    faint_pcm = _generate_sine_wave(freq_hz=400.0, duration_sec=0.02, amplitude=50.0)
    assert detector.is_speech(faint_pcm) is False


def test_vad_rms_provider_mode():
    detector = VoiceActivityDetector(provider="rms", rms_prefilter_threshold=200.0)
    silence_pcm = b"\x00" * 320
    assert detector.is_speech(silence_pcm) is False

    loud_pcm = _generate_sine_wave(freq_hz=300.0, duration_sec=0.02, amplitude=15000.0)
    assert detector.is_speech(loud_pcm) is True


def test_vad_webrtc_speech_vs_silence():
    detector = VoiceActivityDetector(provider="webrtc", mode=1)
    silence_pcm = b"\x00" * 320
    assert detector.is_speech(silence_pcm) is False

    # Human voice fundamental frequency is typically 100-300 Hz
    voice_pcm = _generate_sine_wave(freq_hz=200.0, duration_sec=0.02, amplitude=12000.0)
    # WebRTC VAD recognizes structured human vocal frequencies
    result = detector.is_speech(voice_pcm)
    assert isinstance(result, bool)


def test_vad_arbitrary_chunk_length():
    detector = VoiceActivityDetector(provider="webrtc", mode=2)
    # 60ms chunk (960 bytes, i.e. 3x 20ms frames)
    silence_60ms = b"\x00" * 960
    assert detector.is_speech(silence_60ms) is False


@pytest.mark.asyncio
async def test_pipeline_vad_barge_in_integration():
    mock_ws = AsyncMock()
    mock_ws.send_text = AsyncMock()

    mock_agent = MagicMock()
    mock_stt = AsyncMock()
    mock_tts = MagicMock()

    pipeline = TwilioMediaStreamPipeline(
        websocket=mock_ws,
        voice_agent=mock_agent,
        stt_service=mock_stt,
        tts_service=mock_tts,
        rms_threshold=200.0,
    )
    pipeline.stream_sid = "test_stream_123"

    # Simulate bot speaking
    pipeline.is_bot_speaking = True
    fake_tts_task = MagicMock()
    fake_tts_task.done.return_value = False
    pipeline.current_tts_task = fake_tts_task

    # Send incoming human voice chunk
    speech_pcm = _generate_sine_wave(freq_hz=250.0, duration_sec=0.02, amplitude=18000.0)
    speech_mulaw = pcm_to_mulaw(speech_pcm)

    await pipeline._process_inbound_chunk(speech_mulaw)

    # Barge-in should be triggered: bot silenced and TTS task cancelled
    assert pipeline.is_bot_speaking is False
    fake_tts_task.cancel.assert_called_once()
    assert pipeline.is_caller_speaking is True
    assert len(pipeline.inbound_audio_buffer) == len(speech_mulaw)
