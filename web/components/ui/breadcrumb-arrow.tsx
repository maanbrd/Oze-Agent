export function BreadcrumbArrow({ width = 120 }: { width?: number }) {
  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-block",
        width,
        height: 18,
        filter: "drop-shadow(0 0 4px #3DFF7A77)",
      }}
    >
      <svg viewBox="0 0 220 18" width="100%" height="100%">
        <path
          className="breadcrumb-crawl"
          d="M4 9 L200 9"
          fill="none"
          stroke="#3DFF7A"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeDasharray="5 6"
        />
        <path
          d="M194 3 L212 9 L194 15"
          fill="none"
          stroke="#3DFF7A"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
      {/* React 19: href deduplicates across N instances on the same page */}
      <style href="breadcrumb-arrow" precedence="default">{`
        .breadcrumb-crawl { animation: breadcrumb-crawl 0.8s linear infinite; }
        @keyframes breadcrumb-crawl { to { stroke-dashoffset: -11; } }
        @media (prefers-reduced-motion: reduce) {
          .breadcrumb-crawl { animation: none; }
        }
      `}</style>
    </span>
  );
}
