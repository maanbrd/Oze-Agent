"""OpenAI Whisper speech-to-text for OZE-Agent.

Transcribes Polish voice messages from Telegram.
Cost: ~$0.006/min.
"""

import io

import openai

from bot.config import Config


async def transcribe_voice(audio_bytes: bytes, filename: str = "voice.ogg") -> dict:
    """Transcribe audio using Whisper API.

    Returns:
        {"text": str, "confidence": float, "duration_seconds": float}
    Raises:
        RuntimeError on API failure.
    """
    client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    try:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="pl",
            response_format="verbose_json",
        )

        segments = response.segments if hasattr(response, "segments") else []
        avg_confidence = 1.0
        if segments:
            confidences = [s.get("avg_logprob", -0.3) for s in segments]
            avg_logprob = sum(confidences) / len(confidences)
            avg_confidence = min(1.0, max(0.0, 1.0 + avg_logprob / 0.5))

        return {
            "text": response.text,
            "confidence": avg_confidence,
            "duration_seconds": getattr(response, "duration", 0),
        }
    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {e}") from e
