import Link from "next/link";
import type { CSSProperties } from "react";

export const BRAND_NAME = "Agent OZE";
export const BRAND_GREEN = "#3DFF7A";

type BrandMarkProps = {
  className?: string;
  style?: CSSProperties;
};

export function BrandMark({ className, style }: BrandMarkProps) {
  return (
    <span
      aria-hidden="true"
      className={className}
      style={{
        width: 32,
        height: 32,
        borderRadius: "50%",
        position: "relative",
        border: `2.5px solid ${BRAND_GREEN}`,
        boxShadow: `0 0 16px ${BRAND_GREEN}66, inset 0 0 8px ${BRAND_GREEN}33`,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        ...style,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: BRAND_GREEN,
          boxShadow: `0 0 8px ${BRAND_GREEN}`,
        }}
      />
    </span>
  );
}

type BrandLinkProps = {
  href: string;
  className?: string;
  style?: CSSProperties;
  textClassName?: string;
  textStyle?: CSSProperties;
};

export function BrandLink({
  href,
  className,
  style,
  textClassName,
  textStyle,
}: BrandLinkProps) {
  return (
    <Link
      href={href}
      aria-label={BRAND_NAME}
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        color: "#fff",
        textDecoration: "none",
        ...style,
      }}
    >
      <BrandMark />
      <span
        className={textClassName}
        style={{
          fontWeight: 600,
          fontSize: 17,
          whiteSpace: "nowrap",
          ...textStyle,
        }}
      >
        {BRAND_NAME}
      </span>
    </Link>
  );
}
