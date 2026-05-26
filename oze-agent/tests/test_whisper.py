"""Unit tests for shared/whisper_stt.py — OpenAI calls are mocked."""

from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_transcribe_voice_uses_gpt4o_transcribe_by_default():
    mock_response = MagicMock()
    mock_response.text = "Jan Kowalski, Warszawa, telefon 600 100 200"

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.Config.VOICE_STT_MODEL", "gpt-4o-transcribe"), \
         patch("shared.whisper_stt.Config.VOICE_STT_FALLBACK_MODEL", "whisper-1"), \
         patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(b"fake-audio-bytes")

    kwargs = mock_client.audio.transcriptions.create.await_args.kwargs
    assert kwargs["model"] == "gpt-4o-transcribe"
    assert kwargs["response_format"] == "json"
    assert kwargs["language"] == "pl"
    assert "handlowca OZE" in kwargs["prompt"]
    assert result["text"] == "Jan Kowalski, Warszawa, telefon 600 100 200"
    assert result["confidence"] is None
    assert result["duration_seconds"] == 0.0
    assert result["model"] == "gpt-4o-transcribe"
    assert result["fallback_used"] is False


@pytest.mark.asyncio
async def test_transcribe_voice_whisper_legacy_verbose_json_when_selected():
    mock_response = MagicMock()
    mock_response.text = "Jan Kowalski, Warszawa, telefon 600 100 200"
    mock_response.segments = [{"avg_logprob": -0.1}]
    mock_response.duration = 5.2

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"fake-audio-bytes",
            model="whisper-1",
            allow_fallback=False,
        )

    kwargs = mock_client.audio.transcriptions.create.await_args.kwargs
    assert kwargs["model"] == "whisper-1"
    assert kwargs["response_format"] == "verbose_json"
    assert result["text"] == "Jan Kowalski, Warszawa, telefon 600 100 200"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["duration_seconds"] == 5.2
    assert result["model"] == "whisper-1"
    assert result["fallback_used"] is False


@pytest.mark.asyncio
async def test_transcribe_voice_falls_back_to_whisper_when_primary_fails():
    fallback_response = MagicMock()
    fallback_response.text = "Jan Kowalski"
    fallback_response.segments = [{"avg_logprob": -0.1}]
    fallback_response.duration = 4.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(
        side_effect=[Exception("new model down"), fallback_response]
    )

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="gpt-4o-transcribe",
            fallback_model="whisper-1",
        )

    calls = mock_client.audio.transcriptions.create.await_args_list
    assert calls[0].kwargs["model"] == "gpt-4o-transcribe"
    assert calls[1].kwargs["model"] == "whisper-1"
    assert result["text"] == "Jan Kowalski"
    assert result["model"] == "whisper-1"
    assert result["fallback_used"] is True
    assert result["fallback_from"] == "gpt-4o-transcribe"


@pytest.mark.asyncio
async def test_transcribe_voice_high_confidence_on_good_logprob():
    mock_response = MagicMock()
    mock_response.text = "test"
    mock_response.segments = [{"avg_logprob": -0.05}]
    mock_response.duration = 1.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_transcribe_voice_raises_on_api_error():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API down"))

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        with pytest.raises(RuntimeError, match="Transcription failed"):
            await transcribe_voice(
                b"audio",
                model="gpt-4o-transcribe",
                allow_fallback=False,
            )


@pytest.mark.asyncio
async def test_transcribe_voice_no_segments_defaults_confidence_one():
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.segments = []
    mock_response.duration = 2.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert result["confidence"] == 1.0


# ── SDK 1.50+ compatibility: segments as Pydantic objects (TranscriptionSegment) ──


@pytest.mark.asyncio
async def test_transcribe_voice_handles_object_segments():
    """openai SDK 1.50+ returns Pydantic TranscriptionSegment objects, not dicts."""
    mock_response = MagicMock()
    mock_response.text = "Jan Kowalski"
    mock_response.segments = [SimpleNamespace(avg_logprob=-0.05)]
    mock_response.duration = 3.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_transcribe_voice_handles_missing_avg_logprob_dict():
    """Dict segment missing 'avg_logprob' → fallback default -0.3 → confidence ~0.4."""
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.segments = [{}]
    mock_response.duration = 1.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert 0.3 <= result["confidence"] <= 0.5


@pytest.mark.asyncio
async def test_transcribe_voice_handles_missing_avg_logprob_object():
    """Object segment without avg_logprob attribute → fallback default -0.3."""
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.segments = [SimpleNamespace()]
    mock_response.duration = 1.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert 0.3 <= result["confidence"] <= 0.5


@pytest.mark.asyncio
async def test_transcribe_voice_handles_mixed_segment_types():
    """Heterogeneous list (dict + object) — defensive; SDK is unlikely to return
    mixed but helper must not crash if it ever does."""
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.segments = [
        {"avg_logprob": -0.05},
        SimpleNamespace(avg_logprob=-0.10),
    ]
    mock_response.duration = 2.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(
            b"audio",
            model="whisper-1",
            allow_fallback=False,
        )

    assert result["confidence"] > 0.7


def test_estimate_transcription_cost_for_supported_models():
    from shared.whisper_stt import estimate_transcription_cost

    assert estimate_transcription_cost("gpt-4o-transcribe", 60) == pytest.approx(0.006)
    assert estimate_transcription_cost("gpt-4o-mini-transcribe", 60) == pytest.approx(0.003)
    assert estimate_transcription_cost("whisper-1", 60) == pytest.approx(0.006)
