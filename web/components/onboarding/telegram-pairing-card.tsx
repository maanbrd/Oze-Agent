"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { generateTelegramCodeAction } from "@/app/onboarding/actions";

const TELEGRAM_BOT_HANDLE = "@OZEAGENTBot";
const PAIRING_TTL_SECONDS = 90;
const POLL_INTERVAL_MS = 3000;

type TelegramPollingStatus = {
  paired?: boolean;
};

function remainingFromExpiry(expiresAt: string | null) {
  if (!expiresAt) {
    return PAIRING_TTL_SECONDS;
  }

  const expiryMs = new Date(expiresAt).getTime();
  if (!Number.isFinite(expiryMs)) {
    return PAIRING_TTL_SECONDS;
  }

  const secondsUntilExpiry = Math.ceil((expiryMs - Date.now()) / 1000);
  return Math.max(0, Math.min(PAIRING_TTL_SECONDS, secondsUntilExpiry));
}

export function TelegramPairingCard({
  code,
  expiresAt,
}: {
  code: string | null;
  expiresAt: string | null;
}) {
  const [remainingSeconds, setRemainingSeconds] = useState(() =>
    remainingFromExpiry(expiresAt),
  );
  const command = `/start ${code ?? "KOD"}`;
  const expired = remainingSeconds <= 0;

  useEffect(() => {
    const fallbackExpiresAt = Date.now() + PAIRING_TTL_SECONDS * 1000;
    const parsedExpiresAt = expiresAt ? new Date(expiresAt).getTime() : NaN;
    const targetMs = Number.isFinite(parsedExpiresAt)
      ? Math.min(parsedExpiresAt, fallbackExpiresAt)
      : fallbackExpiresAt;

    function tick() {
      setRemainingSeconds(
        Math.max(0, Math.ceil((targetMs - Date.now()) / 1000)),
      );
    }

    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [code, expiresAt]);

  useEffect(() => {
    if (!code || expired) {
      return;
    }

    let cancelled = false;

    async function pollStatus() {
      try {
        const response = await fetch("/api/onboarding/telegram-status", {
          cache: "no-store",
        });
        if (!response.ok || cancelled) {
          return;
        }

        const status = (await response.json()) as TelegramPollingStatus;
        if (!cancelled && status.paired) {
          window.location.assign("/dashboard?onboarding=complete");
        }
      } catch {
        // Polling is best-effort. The manual refresh button remains available.
      }
    }

    pollStatus();
    const polling = window.setInterval(pollStatus, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(polling);
    };
  }, [code, expired]);

  const timerLabel = useMemo(() => {
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = String(remainingSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }, [remainingSeconds]);

  return (
    <div className="mt-6 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm text-zinc-300">Kod parowania</p>
            <p className="mt-3 text-5xl font-semibold tracking-[0.18em] text-white">
              {code ?? "------"}
            </p>
          </div>
          <div
            className={
              expired
                ? "rounded-[8px] border border-red-400/25 bg-red-400/10 px-4 py-3 text-right"
                : "rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 px-4 py-3 text-right"
            }
          >
            <p className="text-xs font-semibold uppercase text-zinc-400">
              Ważny jeszcze
            </p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-white">
              {timerLabel}
            </p>
            <p className="mt-1 text-xs text-zinc-400">90 sekund na wpisanie kodu</p>
          </div>
        </div>

        <div className="mt-6 rounded-[8px] border border-white/10 bg-black/35 p-4">
          <p className="text-sm text-zinc-400">Bot Telegram</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {TELEGRAM_BOT_HANDLE}
          </p>
        </div>

        <div className="mt-4 rounded-[8px] border border-white/10 bg-black/45 p-4">
          <p className="text-sm text-zinc-400">Wyślij dokładnie tę komendę</p>
          <code className="mt-2 block overflow-x-auto whitespace-nowrap text-xl font-semibold text-white">
            {command}
          </code>
        </div>

        {expired ? (
          <p className="mt-4 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm font-semibold text-red-100">
            Kod wygasł. Wygeneruj nowy kod.
          </p>
        ) : (
          <p className="mt-4 text-sm leading-6 text-zinc-400">
            Nie zamykaj tej strony. Otwórz Telegrama w osobnej karcie albo w
            telefonie i wyślij komendę do bota.
          </p>
        )}

        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <form action={generateTelegramCodeAction}>
            <button
              className={
                expired
                  ? "inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black transition hover:bg-[#6DFF98] sm:w-auto"
                  : "inline-flex w-full items-center justify-center rounded-full border border-[#3DFF7A]/40 px-5 py-3 text-sm font-semibold text-[#3DFF7A] transition hover:border-[#3DFF7A]/70 hover:bg-[#3DFF7A]/10 sm:w-auto"
              }
            >
              Wygeneruj nowy kod
            </button>
          </form>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="inline-flex w-full items-center justify-center rounded-full border border-white/12 px-5 py-3 text-sm font-semibold text-zinc-200 transition hover:border-white/30 hover:text-white sm:w-auto"
          >
            Sprawdź status
          </button>
        </div>
      </section>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <p className="text-sm font-semibold text-white">
          Jak połączyć swojego agenta
        </p>
        <div className="mt-5 overflow-hidden rounded-[8px] border border-white/10 bg-black/30">
          <Image
            src="/media/telegram-pairing-flow.png"
            alt="Instrukcja: Telegram, Komenda, Połączenie, Panel"
            width={1774}
            height={887}
            className="h-auto w-full"
            priority
          />
        </div>

        <ol className="mt-5 space-y-3 text-sm leading-6 text-zinc-300">
          {[
            "Otwórz Telegram.",
            "Kliknij wyszukiwarkę u góry ekranu.",
            "Wpisz @OZEAGENTBot.",
            "Otwórz czat z botem.",
            "Jeśli widzisz przycisk Start, kliknij go.",
            "Skopiuj komendę z tej strony.",
            `Wklej w Telegramie komendę ${command}.`,
            "Wyślij wiadomość do bota.",
            "Wróć tutaj i odśwież stronę, jeśli status nie zmieni się sam.",
          ].map((step, index) => (
            <li key={step} className="flex gap-3">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border border-[#3DFF7A]/30 text-xs font-semibold text-[#3DFF7A]">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
