"use client";

import { Toaster } from "sonner";

export function BrandToaster() {
  return (
    <Toaster
      theme="dark"
      position="bottom-right"
      gap={12}
      toastOptions={{
        style: {
          background: "#0b0d10",
          color: "#f5f7fa",
          border: "1px solid #3DFF7A",
          borderRadius: 12,
          boxShadow:
            "0 0 0 1px #3DFF7A22, 0 0 18px #3DFF7A22, 0 12px 36px #00000088",
          fontSize: 13,
        },
        classNames: {
          error: "sonner-brand-error",
          success: "sonner-brand-success",
        },
      }}
    />
  );
}
