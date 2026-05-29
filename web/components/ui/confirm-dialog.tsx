"use client";

import { useEffect, useState, type ReactNode } from "react";
import { BrandSpinner } from "./brand-spinner";

type Props = {
  open: boolean;
  title: string;
  description?: ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  variant?: "destructive" | "default";
  onConfirm: () => Promise<void> | void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Anuluj",
  variant = "default",
  onConfirm,
  onCancel,
}: Props) {
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !pending) onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, pending, onCancel]);

  if (!open) return null;

  const confirmColor = variant === "destructive" ? "#FF6464" : "#3DFF7A";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      style={{
        position: "fixed",
        inset: 0,
        background: "#000000aa",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 10000,
      }}
    >
      <div
        style={{
          background: "#0b0d10",
          border: `1px solid ${confirmColor}`,
          borderRadius: 14,
          padding: "26px 28px",
          maxWidth: 440,
          width: "calc(100% - 32px)",
          boxShadow: `0 0 0 1px ${confirmColor}22, 0 24px 60px #000`,
          color: "#f5f7fa",
        }}
      >
        <h3 id="confirm-dialog-title" style={{ marginTop: 0, fontSize: 18 }}>
          {title}
        </h3>
        {description && (
          <div style={{ marginTop: 8, color: "#9ca3af", fontSize: 13 }}>
            {description}
          </div>
        )}
        <div style={{ marginTop: 22, display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onCancel}
            disabled={pending}
            style={{
              background: "transparent",
              border: "1px solid #1f242b",
              color: "#9ca3af",
              padding: "10px 16px",
              borderRadius: 999,
              cursor: pending ? "wait" : "pointer",
            }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={async () => {
              setPending(true);
              try {
                await onConfirm();
              } finally {
                setPending(false);
              }
            }}
            style={{
              background: confirmColor,
              color: "#0b0d10",
              padding: "10px 18px",
              borderRadius: 999,
              fontWeight: 600,
              cursor: pending ? "wait" : "pointer",
              border: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            {pending && <BrandSpinner variant="solid" />}
            <span>{confirmLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
