import io
import wave

import pytest

from src.voice.audio_utils import (
    calculate_rms,
    mulaw_to_pcm,
    mulaw_to_wav_bytes,
    pcm_to_mulaw,
)
from src.voice.stt import SpeechToTextService
from src.voice.tts import ElevenLabsTTSService


def test_mulaw_pcm_roundtrip():
    # 8-bit mulaw byte stream
    test_mulaw = bytes([0, 10, 50, 100, 128, 200, 255] * 10)
    pcm = mulaw_to_pcm(test_mulaw)
    assert len(pcm) == len(test_mulaw) * 2

    roundtrip = pcm_to_mulaw(pcm)
    assert len(roundtrip) == len(test_mulaw)


def test_wav_conversion():
    test_mulaw = bytes([128] * 1600)  # 200ms of audio
    wav_bytes = mulaw_to_wav_bytes(test_mulaw, sample_rate=8000)

    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 8000
        assert w.getsampwidth() == 2
        assert w.getnframes() == 1600


def test_rms_calculation():
    # Silence
    silence_pcm = bytes([0] * 320)
    assert calculate_rms(silence_pcm) == 0.0

    # Max volume
    loud_pcm = bytes([255, 127] * 160)
    assert calculate_rms(loud_pcm) > 10000.0


@pytest.mark.asyncio
async def test_elevenlabs_mock_tts():
    # When api_key is None, it safely yields mock audio chunks for testing
    tts = ElevenLabsTTSService(api_key="")
    chunks = []
    async for chunk in tts.stream_speech("Buongiorno e benvenuto a Sina Bernini Bristol"):
        chunks.append(chunk)
        if len(chunks) >= 3:
            break
    assert len(chunks) >= 3
    assert all(len(c) > 0 for c in chunks)


@pytest.mark.asyncio
async def test_stt_empty_audio():
    stt = SpeechToTextService(groq_api_key="", elevenlabs_api_key="")
    res = await stt.transcribe_mulaw(b"")
    assert res == ""
