"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { CrmClient, CrmEvent } from "@/lib/crm/types";
import { formatWarsawDayLabel, formatWarsawTime } from "@/lib/dates";

const G = "#3DFF7A";

export function BriefJutraModal({
  tomorrowKey,
  tomorrowEvents,
  urgentClients,
  decisionsCount,
}: {
  tomorrowKey: string;
  tomorrowEvents: CrmEvent[];
  urgentClients: CrmClient[];
  decisionsCount: number;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="group flex h-full w-full flex-col items-start gap-2 rounded-[8px] border border-white/10 bg-white/[0.04] p-4 text-left transition hover:border-[#3DFF7A]/40 hover:bg-white/[0.06]"
      >
        <span className="text-2xl" aria-hidden="true">📅</span>
        <span className="font-semibold text-white">Brief na jutro</span>
        <span className="text-xs text-zinc-400">
          Spotkania, zaległe akcje, decyzje. Klik = podgląd.
        </span>
      </button>

      {open ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="brief-jutra-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
          className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 p-6 backdrop-blur-sm"
        >
          <div className="w-full max-w-xl rounded-[14px] border border-white/10 bg-[#0b0e12] p-6 text-white shadow-[0_30px_80px_rgba(0,0,0,0.7)]">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#3DFF7A]">
                  📅 Brief na jutro
                </p>
                <h2 id="brief-jutra-title" className="mt-1 text-xl font-semibold">
                  {formatWarsawDayLabel(tomorrowKey)}
                </h2>
              </div>
              <button
                type="button"
                aria-label="Zamknij"
                onClick={() => setOpen(false)}
                className="text-2xl leading-none text-zinc-400 transition hover:text-white"
              >
                ×
              </button>
            </div>

            <Section title={`Spotkania jutro (${tomorrowEvents.length})`} emoji="🗓">
              {tomorrowEvents.length === 0 ? (
                <p className="text-sm text-zinc-500">Jutro bez spotkań w Calendar.</p>
              ) : (
                <ul className="space-y-2">
                  {tomorrowEvents
                    .slice()
                    .sort((a, b) => a.startsAt.localeCompare(b.startsAt))
                    .map((event) => (
                      <li
                        key={event.id}
                        className="rounded-[8px] border border-white/10 bg-black/20 px-3 py-2 text-sm"
                      >
                        <span className="font-semibold text-white">
                          {formatWarsawTime(event.startsAt)} · {event.clientName}
                        </span>
                        {event.title ? (
                          <span className="ml-2 text-zinc-400">{event.title}</span>
                        ) : null}
                      </li>
                    ))}
                </ul>
              )}
            </Section>

            <Section
              title={`Zaległe akcje do dziś (${urgentClients.length})`}
              emoji="⏰"
            >
              {urgentClients.length === 0 ? (
                <p className="text-sm text-zinc-500">Brak zaległych akcji.</p>
              ) : (
                <ul className="space-y-2">
                  {urgentClients.map((client) => (
                    <li
                      key={client.id}
                      className="rounded-[8px] border border-white/10 bg-black/20 px-3 py-2 text-sm"
                    >
                      <span className="font-semibold text-white">{client.fullName}</span>
                      {client.city ? (
                        <span className="text-zinc-400"> · {client.city}</span>
                      ) : null}
                      {client.nextAction ? (
                        <span className="mt-1 block text-amber-200">{client.nextAction}</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title="Wymagają decyzji" emoji="🎯">
              <Link
                href="/dashboard/decyzje-preview"
                onClick={() => setOpen(false)}
                className="flex items-center justify-between rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-4 py-3 text-sm transition hover:border-[#3DFF7A]/60"
              >
                <span className="font-semibold text-white">
                  {decisionsCount === 0
                    ? "Lejek aktualny — zero zaległości"
                    : `${decisionsCount} ${decisionsCount === 1 ? "klient czeka" : "klientów czeka"} na decyzję`}
                </span>
                <span style={{ color: G }} aria-hidden="true">
                  →
                </span>
              </Link>
            </Section>

            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-2 w-full rounded-full border border-white/15 px-5 py-2 text-sm text-zinc-300 transition hover:border-white/30 hover:text-white"
            >
              Zamknij
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}

function Section({
  title,
  emoji,
  children,
}: {
  title: string;
  emoji: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-4">
      <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        <span aria-hidden="true">{emoji}</span>
        {title}
      </h3>
      {children}
    </section>
  );
}
