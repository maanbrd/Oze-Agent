type SparklineProps = {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  ariaLabel?: string;
};

const DEFAULT_WIDTH = 160;
const DEFAULT_HEIGHT = 40;
const PADDING = 4;

export function Sparkline({
  data,
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT,
  color = "#3DFF7A",
  ariaLabel,
}: SparklineProps) {
  if (data.length === 0) {
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={ariaLabel ?? "brak danych"}
      >
        <line
          x1={PADDING}
          y1={height / 2}
          x2={width - PADDING}
          y2={height / 2}
          stroke="rgba(255,255,255,0.15)"
          strokeWidth={1}
          strokeDasharray="3 3"
        />
      </svg>
    );
  }

  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const span = Math.max(max - min, 1);

  const usableW = width - PADDING * 2;
  const usableH = height - PADDING * 2;
  const stepX = data.length > 1 ? usableW / (data.length - 1) : 0;

  const points = data.map((value, i) => {
    const x = PADDING + (data.length === 1 ? usableW / 2 : i * stepX);
    const y = PADDING + usableH - ((value - min) / span) * usableH;
    return { x, y, value };
  });

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ");

  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(2)} ${(height - PADDING).toFixed(2)} L ${points[0].x.toFixed(2)} ${(height - PADDING).toFixed(2)} Z`;

  const last = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel ?? `wartości: ${data.join(", ")}`}
    >
      <path d={areaPath} fill={color} fillOpacity={0.1} />
      <path d={linePath} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
      {points.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r={i === points.length - 1 ? 2.5 : 1.5}
          fill={i === points.length - 1 ? color : "rgba(255,255,255,0.4)"}
        />
      ))}
      <circle cx={last.x} cy={last.y} r={4} fill={color} fillOpacity={0.2} />
    </svg>
  );
}
