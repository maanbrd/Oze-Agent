"use client";

import { useEffect, type ReactNode } from "react";

type StepStatus = "done" | "active" | "pending";
type Step = { label: string; status: StepStatus };

type Props = {
  steps: Step[];
  statusLabel: string;
  subLabel: string;
  nextUrl: string;
  delayMs?: number;
};

export function RedirectingScreen({
  steps,
  statusLabel,
  subLabel,
  nextUrl,
  delayMs = 600,
}: Props) {
  useEffect(() => {
    const id = window.setTimeout(() => {
      window.location.href = nextUrl;
    }, delayMs);
    return () => window.clearTimeout(id);
  }, [nextUrl, delayMs]);

  const stepNodes = (
    steps.map((step, idx) => (
      <div className={`rs-step rs-step-${step.status}`} key={`s-${idx}`}>
        <div className="pill">{step.label}</div>
      </div>
    )).flatMap((node, idx, arr) =>
      idx < arr.length - 1
        ? [
            node,
            <Connector
              key={`c-${idx}`}
              active={steps[idx + 1].status === "active"}
              done={steps[idx + 1].status === "done"}
            />,
          ]
        : [node]
    ) as ReactNode[]
  );

  return (
    <div className="rs-screen" role="status" aria-live="polite">
      <span className="brand-mark" aria-hidden="true" />
      <div className="rs-status">
        {statusLabel}
        <span className="dots" />
      </div>
      <div className="rs-sub">{subLabel}</div>
      <div className="rs-steps">{stepNodes}</div>
      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="rs-screen" precedence="default">{`
        .rs-screen { background: radial-gradient(circle at center, #0b0d10 0%, #050607 70%); min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 24px; color: #f5f7fa; }
        .brand-mark { width: 36px; height: 36px; border: 1.5px solid #3DFF7A; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 26px; box-shadow: 0 0 18px #3DFF7A66; position: relative; }
        .brand-mark::after { content: ""; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background: #3DFF7A; box-shadow: 0 0 8px #3DFF7A; animation: brand-breathe 2.2s ease-in-out infinite; }
        @keyframes brand-breathe { 0%,100% { opacity: 0.55; transform: translate(-50%, -50%) scale(0.9); } 50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); } }
        .rs-status { font-size: 14px; letter-spacing: 0.02em; margin-bottom: 4px; }
        .dots::after { content: "…"; animation: dots-fade 1.4s steps(4, end) infinite; }
        @keyframes dots-fade { 0%{content:"";}25%{content:".";}50%{content:"..";}75%{content:"...";}100%{content:"…";} }
        .rs-sub { font-size: 11px; color: #6b7280; letter-spacing: 0.05em; margin-bottom: 32px; }
        .rs-steps { display: flex; align-items: center; gap: 4px; }
        .rs-step { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 84px; }
        .pill { border: 1.2px solid #1f242b; color: #4a5460; padding: 6px 10px; border-radius: 999px; font-size: 11px; letter-spacing: 0.04em; background: #060709; transition: all 240ms ease; }
        .rs-step-done .pill { border-color: #3DFF7A66; color: #3DFF7A; }
        .rs-step-active .pill { border-color: #3DFF7A; color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A55, 0 0 18px #3DFF7A55; animation: step-breathe 1.6s ease-in-out infinite; }
        @keyframes step-breathe { 0%,100% { box-shadow: 0 0 0 1px #3DFF7A22, 0 0 8px #3DFF7A33; } 50% { box-shadow: 0 0 0 1px #3DFF7A88, 0 0 24px #3DFF7A66; } }
        @media (prefers-reduced-motion: reduce) {
          .brand-mark::after, .rs-step-active .pill, .dots::after { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

function Connector({ active, done }: { active: boolean; done: boolean }) {
  return (
    <div className="rs-conn" aria-hidden="true">
      <svg viewBox="0 0 28 12" preserveAspectRatio="none" width="100%" height="100%">
        <path
          d="M2 6 L26 6"
          stroke={done ? "#3DFF7A66" : "#1f242b"}
          strokeDasharray="3 4"
          strokeWidth="1.3"
          strokeLinecap="round"
          fill="none"
        />
        {active && (
          <path
            d="M2 6 L26 6"
            stroke="#3DFF7A"
            strokeDasharray="4 5"
            strokeWidth="1.3"
            strokeLinecap="round"
            fill="none"
            className="rs-crawl"
          />
        )}
      </svg>
      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="rs-conn" precedence="default">{`
        .rs-conn { width: 28px; height: 12px; }
        .rs-crawl { animation: rs-crawl 0.8s linear infinite; filter: drop-shadow(0 0 2px #3DFF7A77); }
        @keyframes rs-crawl { to { stroke-dashoffset: -9; } }
        @media (prefers-reduced-motion: reduce) { .rs-crawl { animation: none; } }
      `}</style>
    </div>
  );
}
