"""Realistic Polish synthetic client data for E2E scenarios."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


SYNTHETIC_EMAIL_DOMAIN = "e2e-noinbox.local"


POLISH_FIRST_NAMES = (
    "Anna",
    "Jan",
    "Krzysztof",
    "Maria",
    "Tomasz",
    "Magdalena",
    "Piotr",
    "Agnieszka",
    "Marek",
    "Karolina",
    "Robert",
    "Ewa",
)

POLISH_LAST_NAMES = (
    "Nowak",
    "Kowalski",
    "Wiśniewski",
    "Wójcik",
    "Kowalczyk",
    "Kamiński",
    "Lewandowski",
    "Zieliński",
    "Szymański",
    "Woźniak",
    "Dąbrowski",
    "Kozłowski",
)

POLISH_CITIES = (
    "Warszawa",
    "Kraków",
    "Wrocław",
    "Świdnica",
    "Wałbrzych",
    "Jelenia Góra",
    "Legnica",
    "Lublin",
    "Rzeszów",
    "Opole",
)


@dataclass(frozen=True)
class RealisticE2EClient:
    name: str
    city: str
    phone: str
    email: str


def _seed_bytes(run_id: str, suffix: str) -> bytes:
    return hashlib.sha256(f"{run_id}:{suffix}".encode("utf-8")).digest()


def _pick(items: tuple[str, ...], seed: bytes, offset: int) -> str:
    return items[seed[offset] % len(items)]


def _email_suffix(suffix: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", suffix.lower()).strip("-")
    return cleaned or "client"


def realistic_e2e_client(run_id: str, suffix: str) -> RealisticE2EClient:
    seed = _seed_bytes(run_id, suffix)
    first = _pick(POLISH_FIRST_NAMES, seed, 0)
    last = _pick(POLISH_LAST_NAMES, seed, 1)
    city = _pick(POLISH_CITIES, seed, 2)
    phone_tail = int.from_bytes(seed[3:7], "big") % 100_000_000
    return RealisticE2EClient(
        name=f"{first} {last}",
        city=city,
        phone=f"6{phone_tail:08d}",
        email=f"e2e.test.{run_id}.{_email_suffix(suffix)}@{SYNTHETIC_EMAIL_DOMAIN}",
    )
