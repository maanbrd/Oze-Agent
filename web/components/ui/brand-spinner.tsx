type BrandSpinnerProps = {
  variant?: "outline" | "solid";
  size?: number;
  label?: string;
};

export function BrandSpinner({
  variant = "outline",
  size = 22,
  label = "Ładuję",
}: BrandSpinnerProps) {
  const stroke = variant === "solid" ? "#0b0d10" : "#3DFF7A";
  const dropShadow =
    variant === "solid" ? undefined : "drop-shadow(0 0 4px #3DFF7A88)";

  return (
    <span
      role="status"
      aria-live="polite"
      aria-atomic="true"
      style={{ display: "inline-flex", filter: dropShadow }}
    >
      <span className="sr-only">{label}</span>
      <svg
        className="motion-safe-only brand-spinner-svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="motion-safe-only brand-spinner-circle"
          cx="12"
          cy="12"
          r="9"
          fill="none"
          stroke={stroke}
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="50 70"
        />
      </svg>
      <style>{`
        .brand-spinner-svg { animation: brand-spinner-rotate 1.2s linear infinite; }
        .brand-spinner-circle { animation: brand-spinner-dash 1.6s ease-in-out infinite; }
        @keyframes brand-spinner-rotate {
          to { transform: rotate(360deg); }
        }
        @keyframes brand-spinner-dash {
          0%   { stroke-dasharray: 5 120; stroke-dashoffset: 0; }
          50%  { stroke-dasharray: 80 45; stroke-dashoffset: -30; }
          100% { stroke-dasharray: 5 120; stroke-dashoffset: -125; }
        }
        /* Authoritative local fallback — duplicates the global .motion-safe-only
           guard in globals.css so this spinner still respects reduced motion
           when rendered in isolation (e.g. without globals.css loaded). */
        @media (prefers-reduced-motion: reduce) {
          .brand-spinner-svg, .brand-spinner-circle {
            animation: none !important;
          }
        }
      `}</style>
    </span>
  );
}
