"use client";

import { useFormStatus } from "react-dom";
import type { ReactNode } from "react";
import { BrandSpinner } from "./brand-spinner";

type SubmitButtonProps = {
  children: ReactNode;
  pendingLabel: string;
  variant?: "outline" | "solid";
  className?: string;
  fullWidth?: boolean;
};

export function SubmitButton({
  children,
  pendingLabel,
  variant = "outline",
  className = "",
  fullWidth = false,
}: SubmitButtonProps) {
  const { pending } = useFormStatus();

  const base =
    variant === "solid"
      ? "bg-[#3DFF7A] text-[#0b0d10] font-semibold"
      : "bg-[#0b0d10] text-[#f5f7fa] border border-[#3DFF7A]";

  const widthClass = fullWidth ? "w-full justify-center" : "";

  return (
    <button
      type="submit"
      disabled={pending}
      aria-busy={pending}
      className={`inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm transition-opacity disabled:cursor-wait disabled:opacity-80 ${base} ${widthClass} ${className}`.trim()}
      style={{
        boxShadow:
          variant === "outline"
            ? "0 0 0 1px #3DFF7A22, 0 0 18px #3DFF7A22"
            : undefined,
      }}
    >
      {pending && <BrandSpinner variant={variant} label={pendingLabel} />}
      <span>{pending ? pendingLabel : children}</span>
    </button>
  );
}
