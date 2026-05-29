"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
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
  const cancelRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    // Move focus into the dialog on open (safest: cancel button for destructive ops).
    cancelRef.current?.focus();

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !pending) {
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key === "Tab") {
        const cancel = cancelRef.current;
        const confirm = confirmRef.current;
        if (!cancel || !confirm) return;
        // Two-button trap: Tab cycles between cancel and confirm.
        if (e.shiftKey) {
          if (document.activeElement === cancel) {
            e.preventDefault();
            confirm.focus();
          }
        } else {
          if (document.activeElement === confirm) {
            e.preventDefault();
            cancel.focus();
          }
        }
      }
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
            ref={cancelRef}
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
            ref={confirmRef}
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
