"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { showError } from "@/lib/ui/toast";

type StepKey = "sheets" | "calendar" | "drive" | "done";
type StepLabel = { key: Exclude<StepKey, "done">; label: string; status: string };

const STEPS: StepLabel[] = [
  { key: "sheets", label: "Sheets", status: "Tworzę arkusz klientów" },
  { key: "calendar", label: "Kalendarz", status: "Konfiguruję Twój kalendarz" },
  { key: "drive", label: "Drive", status: "Przygotowuję folder na zdjęcia" },
];

function stepState(current: StepKey, target: StepKey): "done" | "active" | "pending" {
  const order: StepKey[] = ["sheets", "calendar", "drive", "done"];
  return order.indexOf(current) > order.indexOf(target)
    ? "done"
    : order.indexOf(current) === order.indexOf(target)
      ? "active"
      : "pending";
}

export function ResourceProgress() {
  const router = useRouter();
  const [current, setCurrent] = useState<StepKey>("sheets");
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let redirectId: number | null = null;

    async function poll() {
      if (redirectId !== null) return; // already redirecting; ignore further polls
      try {
        const res = await fetch("/api/onboarding/resources-progress", { cache: "no-store" });
        if (!res.ok) throw new Error(`status ${res.status}`);
        const payload = (await res.json()) as { step: StepKey; elapsed_ms: number };
        if (cancelled) return;
        setCurrent(payload.step);
        setElapsedMs(payload.elapsed_ms);
        if (payload.step === "done" && redirectId === null) {
          redirectId = window.setTimeout(() => {
            router.push("/onboarding/telegram");
          }, 800);
        }
      } catch (err) {
        if (cancelled) return;
        showError(
          "Nie mogę sprawdzić postępu",
          err instanceof Error ? err.message : "Spróbuję za chwilę.",
        );
      }
    }

    poll();
    const id = window.setInterval(poll, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
      if (redirectId !== null) window.clearTimeout(redirectId);
    };
  }, [router]);

  const elapsedSec = Math.floor(elapsedMs / 1000);
  const activeStep = STEPS.find((s) => stepState(current, s.key) === "active") ?? STEPS[STEPS.length - 1];

  return (
    <div className="rp-canvas">
      <div className="rp-eyebrow">krok 4 z 5 — onboarding</div>
      <h2 className="rp-title">Tworzymy Twoje konto Google</h2>
      <div className="rp-sub">To trwa zwykle 15–30 sekund. Nie odświeżaj strony.</div>

      <div className="rp-steps">
        {(STEPS.map((step, idx) => (
          <Step key={step.key} state={stepState(current, step.key)} label={step.label} icon={step.key} idx={idx} />
        )).flatMap((node, idx, arr) =>
          idx < arr.length - 1
            ? [node, <Connector key={`c-${idx}`} active={stepState(current, STEPS[idx + 1].key) === "active"} done={stepState(current, STEPS[idx + 1].key) === "done" || current === "done"} />]
            : [node]
        ) as ReactNode[])}
      </div>

      <div className="rp-status-row">
        <div className="rp-status">
          {current === "done" ? "Gotowe — przekierowuję" : <>{activeStep.status}<span className="dots" /></>}
        </div>
        <div className="rp-elapsed">
          UPŁYNĘŁO <strong>{elapsedSec} s</strong>
        </div>
      </div>

      <div className="rp-reassure">Operacja jest jednorazowa — robimy ją raz na całe życie konta.</div>

      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="rp-canvas" precedence="default">{`
        .rp-canvas { background: #0b0d10; border: 1px solid #1f242b; border-radius: 16px; padding: 56px 48px 48px; text-align: center; color: #f5f7fa; max-width: 720px; margin: 0 auto; }
        .rp-eyebrow { font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: #3DFF7A; opacity: 0.7; margin-bottom: 14px; }
        .rp-title { font-size: 22px; margin: 0 0 10px; font-weight: 500; }
        .rp-sub { font-size: 13px; color: #6b7280; margin-bottom: 38px; }
        .rp-steps { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 32px auto 0; max-width: 560px; }
        .rp-status-row { margin-top: 36px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
        .rp-status { font-size: 14px; }
        .dots::after { content: "…"; animation: dots-fade 1.4s steps(4, end) infinite; }
        @keyframes dots-fade { 0%{content:"";}25%{content:".";}50%{content:"..";}75%{content:"...";}100%{content:"…";} }
        .rp-elapsed { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #6b7280; }
        .rp-elapsed strong { color: #3DFF7A; font-weight: 500; }
        .rp-reassure { margin-top: 28px; font-size: 11px; color: #4a5460; font-style: italic; max-width: 360px; margin-left: auto; margin-right: auto; opacity: 0.7; }
        @media (prefers-reduced-motion: reduce) { .dots::after { animation: none; content: "…"; } }
      `}</style>
    </div>
  );
}

function Step({ state, label, icon }: { state: "done" | "active" | "pending"; label: string; icon: "sheets" | "calendar" | "drive"; idx?: number }) {
  return (
    <div className={`rp-step rp-step-${state}`}>
      <div className="rp-frame">
        <Icon kind={icon} />
        {state === "done" && <div className="rp-check">✓</div>}
      </div>
      <div className="rp-label">{label}</div>
      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="rp-step" precedence="default">{`
        .rp-step { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 90px; }
        .rp-frame { width: 56px; height: 56px; border: 1.5px solid #1f242b; border-radius: 14px; display: flex; align-items: center; justify-content: center; position: relative; background: #060709; transition: all 240ms ease; }
        .rp-frame svg { width: 26px; height: 26px; stroke: #4a5460; fill: none; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; transition: stroke 240ms ease; }
        .rp-check { position: absolute; bottom: -4px; right: -4px; width: 18px; height: 18px; border-radius: 50%; background: #3DFF7A; color: #0b0d10; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; box-shadow: 0 0 6px #3DFF7A88; }
        .rp-label { font-size: 12px; color: #6b7280; letter-spacing: 0.02em; transition: color 240ms ease; }
        .rp-step-done .rp-frame { border-color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A33; }
        .rp-step-done .rp-frame svg { stroke: #3DFF7A; }
        .rp-step-done .rp-label { color: #f5f7fa; }
        .rp-step-active .rp-frame { border-color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A55, 0 0 22px #3DFF7A55; animation: step-breathe 1.6s ease-in-out infinite; }
        .rp-step-active .rp-frame svg { stroke: #3DFF7A; }
        .rp-step-active .rp-label { color: #3DFF7A; }
        @keyframes step-breathe { 0%,100%{box-shadow: 0 0 0 1px #3DFF7A33, 0 0 12px #3DFF7A33;} 50%{box-shadow: 0 0 0 1px #3DFF7A88, 0 0 26px #3DFF7A66;} }
        @media (prefers-reduced-motion: reduce) { .rp-step-active .rp-frame { animation: none; } }
      `}</style>
    </div>
  );
}

function Connector({ active, done }: { active: boolean; done: boolean }) {
  return (
    <div className={`rp-conn ${done ? "rp-conn-done" : active ? "rp-conn-active" : "rp-conn-pending"}`}>
      <svg viewBox="0 0 120 16" preserveAspectRatio="none" width="100%" height="100%">
        <path d="M2 8 L110 8" className="rail" />
        {active && <path d="M2 8 L110 8" className="crawl" />}
        {done && <path d="M104 3 L114 8 L104 13" className="head" />}
      </svg>
      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="rp-connector" precedence="default">{`
        .rp-conn { flex: 1; height: 16px; max-width: 120px; align-self: center; margin-bottom: 24px; }
        .rp-conn svg path { fill: none; stroke-linecap: round; stroke-width: 1.4; }
        .rail { stroke: #1f242b; stroke-dasharray: 4 5; }
        .rp-conn-done .rail { stroke: #3DFF7A66; }
        .crawl { stroke: #3DFF7A; stroke-dasharray: 5 6; animation: connector-crawl 0.8s linear infinite; filter: drop-shadow(0 0 3px #3DFF7A77); }
        .head { stroke: #3DFF7A66; filter: drop-shadow(0 0 3px #3DFF7A77); }
        @keyframes connector-crawl { to { stroke-dashoffset: -11; } }
        @media (prefers-reduced-motion: reduce) { .crawl { animation: none; } }
      `}</style>
    </div>
  );
}

function Icon({ kind }: { kind: "sheets" | "calendar" | "drive" }) {
  switch (kind) {
    case "sheets":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="3" y1="15" x2="21" y2="15" />
          <line x1="9" y1="3" x2="9" y2="21" />
          <line x1="15" y1="3" x2="15" y2="21" />
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <line x1="3" y1="10" x2="21" y2="10" />
          <line x1="8" y1="3" x2="8" y2="7" />
          <line x1="16" y1="3" x2="16" y2="7" />
        </svg>
      );
    case "drive":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 4 L17 4 L22 13 L17 22 L7 22 L2 13 Z" />
          <line x1="7" y1="4" x2="12" y2="13" />
          <line x1="17" y1="4" x2="12" y2="13" />
          <line x1="2" y1="13" x2="22" y2="13" />
        </svg>
      );
  }
}
