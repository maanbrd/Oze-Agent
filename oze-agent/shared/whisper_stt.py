"""OpenAI speech-to-text for OZE-Agent.

Transcribes Polish voice messages from Telegram.
"""

import io

import openai

from bot.config import Config

OPENAI_TIMEOUT_SECONDS = 60.0
OPENAI_MAX_RETRIES = 2
DEFAULT_VOICE_STT_MODEL = "gpt-4o-transcribe"
DEFAULT_VOICE_STT_FALLBACK_MODEL = "whisper-1"

VOICE_STT_PROMPT = (
    "Transkrypcja dotyczy polskiego handlowca OZE rozmawiającego z asystentem CRM. "
    "Zachowaj dokładnie imiona, nazwiska, miejscowości, adresy, numery telefonów, "
    "daty i godziny. Typowe słowa: klient, spotkanie, telefon, fotowoltaika, PV, "
    "magazyn energii, pompa ciepła, follow-up, oferta, wyślij ofertę."
)

_TRANSCRIPTION_COST_PER_MINUTE_USD = {
    "whisper-1": 0.006,
    "gpt-4o-transcribe": 0.006,
    "gpt-4o-transcribe-diarize": 0.006,
    "gpt-4o-mini-transcribe": 0.003,
}


def _segment_avg_logprob(segment, default: float = -0.3) -> float:
    """Extract avg_logprob from a Whisper segment, compatible with both
    dict (legacy / test mocks) and Pydantic TranscriptionSegment object
    (openai SDK 1.50+)."""
    if isinstance(segment, dict):
        return segment.get("avg_logprob", default)
    return getattr(segment, "avg_logprob", default)


def _is_gpt4o_transcribe_model(model: str) -> bool:
    return model.startswith("gpt-4o") and "transcribe" in model


def _audio_file(audio_bytes: bytes, filename: str) -> io.BytesIO:
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    return audio_file


def _response_text(response) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return str(response.get("text", ""))
    text = getattr(response, "text", "")
    return text if isinstance(text, str) else ""


def _response_duration_seconds(response) -> float:
    if isinstance(response, dict):
        value = response.get("duration", 0.0)
    else:
        value = getattr(response, "duration", 0.0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def estimate_transcription_cost(model: str, duration_seconds: float) -> float:
    """Return the estimated transcription cost for internal interaction logs."""
    safe_duration = max(0.0, float(duration_seconds or 0.0))
    rate = _TRANSCRIPTION_COST_PER_MINUTE_USD.get(model, 0.0)
    return (safe_duration / 60.0) * rate


async def _transcribe_with_model(
    client,
    audio_bytes: bytes,
    *,
    filename: str,
    model: str,
    prompt: str,
) -> dict:
    if _is_gpt4o_transcribe_model(model):
        response = await client.audio.transcriptions.create(
            model=model,
            file=_audio_file(audio_bytes, filename),
            language="pl",
            prompt=prompt,
            response_format="json",
        )
        return {
            "text": _response_text(response),
            "confidence": None,
            "duration_seconds": _response_duration_seconds(response),
            "model": model,
            "fallback_used": False,
        }

    response = await client.audio.transcriptions.create(
        model=model,
        file=_audio_file(audio_bytes, filename),
        language="pl",
        prompt=prompt,
        response_format="verbose_json",
    )

    segments = response.segments if hasattr(response, "segments") else []
    avg_confidence = 1.0
    if segments:
        confidences = [_segment_avg_logprob(s) for s in segments]
        avg_logprob = sum(confidences) / len(confidences)
        avg_confidence = min(1.0, max(0.0, 1.0 + avg_logprob / 0.5))

    return {
        "text": _response_text(response),
        "confidence": avg_confidence,
        "duration_seconds": _response_duration_seconds(response),
        "model": model,
        "fallback_used": False,
    }


async def transcribe_voice(
    audio_bytes: bytes,
    filename: str = "voice.ogg",
    *,
    model: str | None = None,
    fallback_model: str | None = None,
    prompt: str = VOICE_STT_PROMPT,
    allow_fallback: bool = True,
) -> dict:
    """Transcribe audio using the configured OpenAI STT model.

    Returns:
        {
            "text": str,
            "confidence": float | None,
            "duration_seconds": float,
            "model": str,
            "fallback_used": bool,
        }
    Raises:
        RuntimeError on API failure.
    """
    client = openai.AsyncOpenAI(
        api_key=Config.OPENAI_API_KEY,
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )
    selected_model = (
        model
        or Config.VOICE_STT_MODEL
        or DEFAULT_VOICE_STT_MODEL
    )
    selected_fallback = (
        fallback_model
        or Config.VOICE_STT_FALLBACK_MODEL
        or DEFAULT_VOICE_STT_FALLBACK_MODEL
    )

    try:
        return await _transcribe_with_model(
            client,
            audio_bytes,
            filename=filename,
            model=selected_model,
            prompt=prompt,
        )
    except Exception as e:
        if allow_fallback and selected_fallback and selected_fallback != selected_model:
            try:
                result = await _transcribe_with_model(
                    client,
                    audio_bytes,
                    filename=filename,
                    model=selected_fallback,
                    prompt=prompt,
                )
            except Exception as fallback_error:
                raise RuntimeError(
                    "Transcription failed with "
                    f"{selected_model} ({e}); fallback {selected_fallback} "
                    f"also failed ({fallback_error})"
                ) from fallback_error
            result["fallback_used"] = True
            result["fallback_from"] = selected_model
            return result
        raise RuntimeError(f"Transcription failed with {selected_model}: {e}") from e
