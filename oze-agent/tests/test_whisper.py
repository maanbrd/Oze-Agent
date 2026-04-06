"""Unit tests for shared/whisper_stt.py — OpenAI calls are mocked."""

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
