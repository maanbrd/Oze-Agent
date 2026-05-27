"""Unit tests for scripts/benchmark_voice_stt.py pure helpers."""

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import AsyncMock, patch

import pytest


def test_load_cases_resolves_audio_paths_relative_to_manifest(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({
            "audio_path": "samples/jan.ogg",
            "expected": {"name": "Jan Kowalski", "city": "Warszawa"},
        }) + "\n",
        encoding="utf-8",
    )

    from scripts.benchmark_voice_stt import load_cases

    [case] = load_cases(manifest)

    assert case.audio_path == tmp_path / "samples/jan.ogg"
    assert case.expected["name"] == "Jan Kowalski"


def test_score_transcript_counts_expected_crm_fields():
    from scripts.benchmark_voice_stt import score_transcript

    score = score_transcript(
        "Dodaj spotkanie z Janem Kowalskim w Warszawie. Telefon 600 100 200. "
        "Interesuje go fotowoltaika i magazyn energii.",
        {
            "intent": "add_meeting",
            "name": "Jan Kowalski",
            "city": "Warszawa",
            "phone": "600100200",
            "product_or_next_action": "magazyn energii",
        },
    )

    assert score.total == 5
    assert score.matched == 5
    assert score.ratio == 1.0
    assert score.missing == []


def test_score_transcript_reports_missing_fields():
    from scripts.benchmark_voice_stt import score_transcript

    score = score_transcript(
        "Dodaj klienta Jan Nowak.",
        {"intent": "add_meeting", "city": "Kraków", "phone": "600100200"},
    )

    assert score.total == 3
    assert score.matched == 0
    assert score.ratio == 0.0
    assert score.missing == ["intent", "city", "phone"]


def test_score_extracted_fields_counts_expected_crm_fields():
    from scripts.benchmark_voice_stt import score_extracted_fields

    score = score_extracted_fields(
        {
            "intent": "add_meeting",
            "name": "Jan Kowalski",
            "city": "Warszawa",
            "phone": "600100200",
            "email": "jan.kowalski@gmail.com",
            "product_or_next_action": "PV + Magazyn energii",
        },
        {
            "intent": "add_meeting",
            "name": "Jan Kowalski",
            "city": "Warszawa",
            "phone": "600 100 200",
            "email": "jan.kowalski małpa gmail kropka com",
            "product_or_next_action": "magazyn energii",
        },
    )

    assert score.total == 6
    assert score.matched == 6
    assert score.ratio == 1.0
    assert score.missing == []


def test_score_extracted_fields_accepts_manifest_date_time_alias():
    from scripts.benchmark_voice_stt import score_extracted_fields

    score = score_extracted_fields(
        {"date": "2026-05-28", "time": "14:00"},
        {"date/time": "2026-05-28 14:00"},
    )

    assert score.ratio == 1.0
    assert score.missing == []


@pytest.mark.asyncio
async def test_benchmark_case_scores_model_by_extracted_fields(tmp_path):
    from scripts.benchmark_voice_stt import BenchmarkCase, _benchmark_case

    audio = tmp_path / "sample.ogg"
    audio.write_bytes(b"fake-audio")
    case = BenchmarkCase(
        audio_path=audio,
        expected={
            "intent": "add_meeting",
            "name": "Jan Kowalski",
            "phone": "600100200",
        },
    )

    with patch(
        "scripts.benchmark_voice_stt.transcribe_voice",
        new=AsyncMock(return_value={
            "text": "tekst z błędnym telefonem",
            "duration_seconds": 3.0,
        }),
    ), patch(
        "scripts.benchmark_voice_stt.extract_voice_fields",
        new=AsyncMock(return_value={
            "fields": {
                "intent": "add_meeting",
                "name": "Jan Kowalski",
                "phone": "600100200",
            },
            "fallback": None,
            "cost_usd": 0.0002,
            "model": "claude-haiku-4-5-20251001",
        }),
    ):
        report = await _benchmark_case(case, ("gpt-4o-transcribe",), score_mode="extracted")

    result = report["results"][0]
    assert result["score"]["ratio"] == 1.0
    assert result["transcript_score"]["ratio"] < 1.0
    assert result["extraction"]["fields"]["phone"] == "600100200"


def test_script_help_runs_when_executed_directly():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "benchmark_voice_stt.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Compare OpenAI STT models" in result.stdout
