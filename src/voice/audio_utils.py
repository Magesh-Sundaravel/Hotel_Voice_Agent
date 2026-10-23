import io
import math
import struct
import wave


def _build_mulaw_to_pcm_table() -> list[int]:
    """Precompute standard G.711 mu-law to 16-bit linear PCM conversion table."""
    table = []
    for i in range(256):
        mu = ~i & 0xFF
        sign = -1 if (mu & 0x80) else 1
        exponent = (mu >> 4) & 0x07
        mantissa = mu & 0x0F
        linear = ((mantissa << 3) + 0x84) << exponent
        linear -= 0x84
        table.append(sign * linear)
    return table


MULAW_TO_PCM_TABLE = _build_mulaw_to_pcm_table()


def mulaw_to_pcm(mulaw_bytes: bytes) -> bytes:
    """Converts 8kHz 8-bit mu-law audio to 8kHz 16-bit linear PCM."""
    if not mulaw_bytes:
        return b""
    # Pack each 16-bit integer into little-endian bytes
    pcm_samples = [MULAW_TO_PCM_TABLE[b] for b in mulaw_bytes]
    return struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)


def pcm_to_mulaw(pcm_bytes: bytes) -> bytes:
    """Converts 16-bit linear PCM to 8-bit G.711 mu-law."""
    if not pcm_bytes:
        return b""
    num_samples = len(pcm_bytes) // 2
    samples = struct.unpack(f"<{num_samples}h", pcm_bytes)
    result = bytearray(num_samples)

    BIAS = 0x84
    CLIP = 32635

    for idx, sample in enumerate(samples):
        sign = 0x80 if sample < 0 else 0
        if sample < 0:
            sample = -sample
        sample = min(sample, CLIP)
        sample += BIAS

        exponent = 7
        for exp in range(7):
            if sample <= (0x1F << (exp + 3)):
                exponent = exp
                break

        mantissa = (sample >> (exponent + 3)) & 0x0F
        byte_val = ~(sign | (exponent << 4) | mantissa) & 0xFF
        result[idx] = byte_val

    return bytes(result)


def pcm_to_wav_bytes(
    pcm_bytes: bytes,
    sample_rate: int = 8000,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Wraps raw 16-bit PCM bytes into an in-memory WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buf.getvalue()


def mulaw_to_wav_bytes(mulaw_bytes: bytes, sample_rate: int = 8000) -> bytes:
    """Converts G.711 mu-law bytes into a 16-bit linear PCM WAV container."""
    pcm = mulaw_to_pcm(mulaw_bytes)
    return pcm_to_wav_bytes(pcm, sample_rate=sample_rate)


def calculate_rms(pcm_bytes: bytes) -> float:
    """Calculates RMS (Root Mean Square) energy of 16-bit PCM samples.

    Returns a value roughly between 0.0 (silence) and 32767.0 (max loudness).
    """
    if len(pcm_bytes) < 2:
        return 0.0
    num_samples = len(pcm_bytes) // 2
    samples = struct.unpack(f"<{num_samples}h", pcm_bytes)
    sum_squares = sum(s * s for s in samples)
    return math.sqrt(sum_squares / num_samples)
