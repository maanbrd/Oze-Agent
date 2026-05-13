"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { generateTelegramCodeAction } from "@/app/onboarding/actions";

const PAIRING_TTL_SECONDS = 90;
const POLL_INTERVAL_MS = 3000;

type TelegramPollingStatus = {
  ok?: boolean;
  paired?: boolean;
  error?: string;
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
  botHandle,
  code,
  expiresAt,
}: {
  botHandle: string;
  code: string | null;
  expiresAt: string | null;
}) {
  const [remainingSeconds, setRemainingSeconds] = useState(() =>
    remainingFromExpiry(expiresAt),
  );
  const [statusError, setStatusError] = useState<string | null>(null);
  const [copyLabel, setCopyLabel] = useState("Kopiuj komendę");
  const command = code ? `/start ${code}` : "";
  const commandLabel = command || "Wygeneruj kod, aby zobaczyć komendę";
  const botUsername = botHandle.replace(/^@+/, "");
  const telegramDeepLink = code
    ? `https://t.me/${botUsername}?start=${encodeURIComponent(code)}`
    : `https://t.me/${botUsername}`;
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

  const pollStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/onboarding/telegram-status", {
        cache: "no-store",
      });
      const status = (await response.json().catch(() => null)) as
        | TelegramPollingStatus
        | null;

      if (!response.ok || !status || status.ok === false) {
        setStatusError("Nie udało się sprawdzić statusu. Spróbujemy ponownie.");
        return;
      }

      setStatusError(null);
      if (status.paired) {
        window.location.assign("/dashboard?onboarding=complete");
      }
    } catch {
      setStatusError("Nie udało się sprawdzić statusu. Spróbujemy ponownie.");
    }
  }, []);

  useEffect(() => {
    if (!code || expired) {
      return;
    }

    const initialPoll = window.setTimeout(pollStatus, 0);
    const polling = window.setInterval(pollStatus, POLL_INTERVAL_MS);
    return () => {
      window.clearTimeout(initialPoll);
      window.clearInterval(polling);
    };
  }, [code, expired, pollStatus]);

  const timerLabel = useMemo(() => {
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = String(remainingSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }, [remainingSeconds]);

  const copyCommand = useCallback(async () => {
    if (!command) {
      return;
    }

    try {
      await navigator.clipboard.writeText(command);
      setCopyLabel("Skopiowano");
      window.setTimeout(() => setCopyLabel("Kopiuj komendę"), 1800);
    } catch {
      setCopyLabel("Skopiuj ręcznie");
    }
  }, [command]);

  return (
    <div className="mt-6 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <div className="rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 p-4">
          <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
            Najprościej na telefonie
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-[180px_1fr] sm:items-center">
            <div className="grid aspect-square w-full max-w-[180px] place-items-center rounded-[8px] bg-white p-3">
              {code && !expired ? (
                <QRCodeSVG
                  value={telegramDeepLink}
                  size={156}
                  bgColor="#ffffff"
                  fgColor="#050607"
                  level="M"
                  marginSize={1}
                />
              ) : (
                <div className="grid h-full w-full place-items-center rounded-[6px] bg-zinc-100 text-center text-xs font-semibold text-zinc-500">
                  Wygeneruj kod
                </div>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-white">
                QR wysyła kod automatycznie.
              </h2>
              <p className="mt-3 text-sm leading-6 text-zinc-300">
                Otwórz Telegrama, kliknij Start i wróć tutaj. Telegram może
                pokazać tylko /start, ale pełny kod parowania jest ukryty w
                linku i trafia do bota automatycznie.
              </p>
              <a
                href={telegramDeepLink}
                target="_blank"
                rel="noreferrer"
                className={
                  code && !expired
                    ? "mt-4 inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black transition hover:bg-[#6DFF98] sm:w-auto"
                    : "pointer-events-none mt-4 inline-flex w-full items-center justify-center rounded-full border border-white/10 px-5 py-3 text-sm font-semibold text-zinc-500 sm:w-auto"
                }
                aria-disabled={!code || expired}
              >
                Otwórz Telegrama z kodem
              </a>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
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
            <p className="mt-1 text-xs text-zinc-400">90 sekund na kliknięcie Start</p>
          </div>
        </div>

        <div className="mt-6 rounded-[8px] border border-white/10 bg-black/35 p-4">
          <p className="text-sm text-zinc-400">Bot Telegram</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {botHandle}
          </p>
        </div>

        <div className="mt-4 rounded-[8px] border border-white/10 bg-black/45 p-4">
          <p className="text-sm text-zinc-400">
            Awaryjnie, jeśli link nie zadziała
          </p>
          <code className="mt-2 block overflow-x-auto whitespace-nowrap text-xl font-semibold text-white">
            {commandLabel}
          </code>
          <button
            type="button"
            onClick={copyCommand}
            disabled={!command}
            className="mt-4 inline-flex w-full items-center justify-center rounded-full border border-white/12 px-4 py-2.5 text-sm font-semibold text-zinc-200 transition hover:border-white/30 hover:text-white disabled:cursor-not-allowed disabled:text-zinc-600 sm:w-auto"
          >
            {copyLabel}
          </button>
        </div>

        {expired ? (
          <p className="mt-4 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm font-semibold text-red-100">
            Kod wygasł. Wygeneruj nowy kod.
          </p>
        ) : statusError ? (
          <p className="mt-4 rounded-[8px] border border-yellow-400/20 bg-yellow-400/10 px-4 py-3 text-sm font-semibold text-yellow-100">
            {statusError}
          </p>
        ) : (
          <p className="mt-4 text-sm leading-6 text-zinc-400">
            Nie wpisuj kodu ponownie, jeśli Telegram pokazał samo /start. Wróć
            tutaj i poczekaj kilka sekund na automatyczne potwierdzenie.
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
            onClick={pollStatus}
            className="inline-flex w-full items-center justify-center rounded-full border border-white/12 px-5 py-3 text-sm font-semibold text-zinc-200 transition hover:border-white/30 hover:text-white sm:w-auto"
          >
            Sprawdź status
          </button>
        </div>
      </section>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <p className="text-sm font-semibold text-white">Co zrobić krok po kroku</p>
        <div className="mt-5 grid gap-3 rounded-[8px] border border-white/10 bg-black/30 p-4 sm:grid-cols-4">
          <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-3">
            <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
              Telefon
            </p>
            <div className="mt-4 h-2 rounded-full bg-white/15" />
            <div className="mt-2 h-2 w-2/3 rounded-full bg-[#3DFF7A]/70" />
          </div>
          <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-3">
            <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
              Bot
            </p>
            <p className="mt-4 truncate text-sm font-semibold text-white">
              {botHandle}
            </p>
          </div>
          <div className="rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-3">
            <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
              Kod w linku
            </p>
            <code className="mt-4 block overflow-hidden text-ellipsis whitespace-nowrap text-sm font-semibold text-white">
              {commandLabel}
            </code>
          </div>
          <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-3">
            <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
              Połączenie
            </p>
            <p className="mt-4 text-sm font-semibold text-white">Panel CRM</p>
          </div>
        </div>

        <ol className="mt-5 space-y-3 text-sm leading-6 text-zinc-300">
          {[
            "Zeskanuj QR telefonem albo kliknij Otwórz Telegrama z kodem.",
            `Telegram otworzy czat z botem ${botHandle}.`,
            "Kliknij Start, jeśli Telegram pokaże taki przycisk.",
            "Jeśli w czacie widzisz tylko /start, to normalne - kod jest w linku.",
            "Wróć tutaj. Panel sam sprawdzi, czy konto jest połączone.",
            "Tylko awaryjnie skopiuj ręcznie komendę z pola po lewej.",
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
