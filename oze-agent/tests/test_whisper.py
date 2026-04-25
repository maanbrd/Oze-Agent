"""Unit tests for shared/whisper_stt.py — OpenAI calls are mocked."""

from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_transcribe_voice_returns_text():
    mock_response = MagicMock()
    mock_response.text = "Jan Kowalski, Warszawa, telefon 600 100 200"
    mock_response.segments = [{"avg_logprob": -0.1}]
    mock_response.duration = 5.2

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        result = await transcribe_voice(b"fake-audio-bytes")

    assert result["text"] == "Jan Kowalski, Warszawa, telefon 600 100 200"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["duration_seconds"] == 5.2


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
        result = await transcribe_voice(b"audio")

    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_transcribe_voice_raises_on_api_error():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API down"))

    with patch("shared.whisper_stt.openai.AsyncOpenAI", return_value=mock_client):
        from shared.whisper_stt import transcribe_voice
        with pytest.raises(RuntimeError, match="Whisper transcription failed"):
            await transcribe_voice(b"audio")


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
        result = await transcribe_voice(b"audio")

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
        result = await transcribe_voice(b"audio")

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
        result = await transcribe_voice(b"audio")

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
        result = await transcribe_voice(b"audio")

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
        result = await transcribe_voice(b"audio")

    assert result["confidence"] > 0.7
