"""Benchmark OpenAI STT models on local, fictional voice samples.

Expected manifest JSONL format:
{"audio_path":"samples/jan.ogg","expected":{"intent":"add_meeting","name":"Jan Kowalski"}}

Keep samples and reports under tests_e2e/.voice_benchmark/; that directory is
gitignored because it may contain local audio files.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.whisper_stt import transcribe_voice

DEFAULT_MODELS = (
    "whisper-1",
    "gpt-4o-mini-transcribe",
    "gpt-4o-transcribe",
)
DEFAULT_MANIFEST = Path("tests_e2e/.voice_benchmark/manifest.jsonl")


@dataclass(frozen=True)
class BenchmarkCase:
    audio_path: Path
    expected: dict[str, str]


@dataclass(frozen=True)
class FieldScore:
    matched: int
    total: int
    ratio: float
    missing: list[str]


def load_cases(manifest_path: Path) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    manifest_dir = manifest_path.parent
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            audio_path = Path(payload["audio_path"])
            if not audio_path.is_absolute():
                audio_path = manifest_dir / audio_path
            expected = {
                str(key): str(value)
                for key, value in payload.get("expected", {}).items()
                if str(value).strip()
            }
            if not expected:
                raise ValueError(f"line {line_no}: expected must not be empty")
            cases.append(BenchmarkCase(audio_path=audio_path, expected=expected))
    return cases


def _norm(text: str) -> str:
    return text.casefold()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\wąćęłńóśźż]+", _norm(text))


def _digits(text: str) -> str:
    return re.sub(r"\D+", "", text)


def _phrase_matches(transcript: str, expected: str) -> bool:
    transcript_norm = _norm(transcript)
    expected_norm = _norm(expected)
    if expected_norm in transcript_norm:
        return True

    transcript_tokens = _tokens(transcript)
    for expected_token in _tokens(expected):
        stem = expected_token[: max(3, len(expected_token) - 2)]
        if not any(token.startswith(stem) for token in transcript_tokens):
            return False
    return True


def _intent_matches(transcript: str, expected: str) -> bool:
    text = _norm(transcript)
    markers = {
        "add_client": ("dodaj klienta", "nowy klient", "klient"),
        "add_meeting": ("spotkanie", "umów", "umow", "termin", "wizyta"),
        "add_note": ("notatka", "dopisz", "zanotuj"),
        "change_status": ("status", "podpisane", "rezygnacja"),
        "send_offer": ("wyślij ofert", "wyslij ofert", "oferta"),
    }
    return any(marker in text for marker in markers.get(expected, (expected,)))


def _field_matches(transcript: str, field: str, expected: str) -> bool:
    if field == "phone":
        expected_digits = _digits(expected)
        return bool(expected_digits) and expected_digits in _digits(transcript)
    if field == "intent":
        return _intent_matches(transcript, expected)
    return _phrase_matches(transcript, expected)


def score_transcript(transcript: str, expected: dict[str, str]) -> FieldScore:
    total = len(expected)
    missing = [
        field
        for field, value in expected.items()
        if not _field_matches(transcript, field, value)
    ]
    matched = total - len(missing)
    ratio = matched / total if total else 0.0
    return FieldScore(matched=matched, total=total, ratio=ratio, missing=missing)


async def _benchmark_case(case: BenchmarkCase, models: Iterable[str]) -> dict:
    audio_bytes = case.audio_path.read_bytes()
    results = []
    for model in models:
        result = await transcribe_voice(
            audio_bytes,
            filename=case.audio_path.name,
            model=model,
            fallback_model="",
            allow_fallback=False,
        )
        score = score_transcript(result["text"], case.expected)
        results.append({
            "model": model,
            "text": result["text"],
            "score": asdict(score),
            "duration_seconds": result.get("duration_seconds", 0.0),
        })
    return {
        "audio_path": str(case.audio_path),
        "expected": case.expected,
        "results": results,
    }


def _summarize(case_reports: list[dict], models: Iterable[str]) -> dict:
    summary = {}
    for model in models:
        scores = [
            result["score"]["ratio"]
            for case in case_reports
            for result in case["results"]
            if result["model"] == model
        ]
        summary[model] = {
            "cases": len(scores),
            "average_field_score": sum(scores) / len(scores) if scores else 0.0,
        }
    return summary


async def run_benchmark(manifest: Path, models: tuple[str, ...], output: Path) -> dict:
    cases = load_cases(manifest)
    if not cases:
        raise ValueError(f"manifest has no cases: {manifest}")

    reports = [await _benchmark_case(case, models) for case in cases]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest),
        "models": list(models),
        "summary": _summarize(reports, models),
        "cases": reports,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _default_output(manifest: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return manifest.parent / "reports" / f"voice-stt-benchmark-{stamp}.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python scripts/benchmark_voice_stt.py",
        description="Compare OpenAI STT models on fictional local voice samples.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output = args.output or _default_output(args.manifest)
    payload = asyncio.run(run_benchmark(args.manifest, tuple(args.models), output))
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
