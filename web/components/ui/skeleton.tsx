import type { ReactNode } from "react";

type LineVariant = "title" | "sub" | "body";

const lineStyles: Record<LineVariant, { height: string; width: string; opacity?: number }> = {
  title: { height: "18px", width: "60%" },
  sub: { height: "12px", width: "40%", opacity: 0.5 },
  body: { height: "12px", width: "90%" },
};

/**
 * Outline-pulse placeholder line for a single piece of text.
 *
 * MUST be rendered inside a `<SkeletonCard>` — the parent injects the shared
 * `.sk-line` keyframe CSS. A standalone `<SkeletonLine />` renders an
 * unstyled zero-height div.
 */
export function SkeletonLine({
  variant = "body",
  delay = 0,
}: {
  variant?: "title" | "sub" | "body";
  delay?: number;
}) {
  const s = lineStyles[variant];
  return (
    <div
      className="sk-line"
      style={{
        height: s.height,
        width: s.width,
        opacity: s.opacity ?? 1,
        animationDelay: `${delay}ms`,
      }}
    />
  );
}

/**
 * Outline-pulse placeholder for a CTA button area.
 *
 * MUST be rendered inside a `<SkeletonCard>` — the parent injects the shared
 * `.sk-cta` keyframe CSS. A standalone `<SkeletonCta />` renders an
 * unstyled empty div.
 */
export function SkeletonCta({ delay = 0 }: { delay?: number }) {
  return (
    <div
      className="sk-line sk-cta"
      style={{ animationDelay: `${delay}ms` }}
      aria-hidden="true"
    />
  );
}

export function SkeletonCard({ children }: { children: ReactNode }) {
  return (
    <div className="sk-card" role="status" aria-label="Ładuję zawartość">
      {children}
      <style href="sk-card" precedence="default">{`
        .sk-card {
          border: 1.5px solid #3DFF7A;
          border-radius: 14px;
          padding: 26px 24px;
          background: linear-gradient(180deg, #0b0d10 0%, #060709 100%);
          box-shadow: 0 0 18px #3DFF7A14;
        }
        .sk-line {
          border: 1px solid #3DFF7A;
          border-radius: 6px;
          margin-bottom: 12px;
          animation: sk-pulse 1.6s ease-in-out infinite;
        }
        .sk-cta {
          height: 38px;
          width: 50%;
          border-radius: 999px;
          margin-top: 20px;
        }
        @keyframes sk-pulse {
          0%, 100% { border-color: #3DFF7A22; box-shadow: none; }
          50%      { border-color: #3DFF7A; box-shadow: 0 0 8px #3DFF7A44; }
        }
        @media (prefers-reduced-motion: reduce) {
          .sk-line { animation: none; border-color: #3DFF7A55; }
        }
      `}</style>
    </div>
  );
}
