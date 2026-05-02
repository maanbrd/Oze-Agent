"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const TELEGRAM_STATUS_POLL_MS = 5000;

export function TelegramStatusPoller() {
  const router = useRouter();

  useEffect(() => {
    const interval = window.setInterval(() => {
      router.refresh();
    }, TELEGRAM_STATUS_POLL_MS);

    return () => window.clearInterval(interval);
  }, [router]);

  return (
    <p className="mt-3 text-sm text-zinc-400">
      Po sparowaniu odświeżymy ten krok automatycznie.
    </p>
  );
}
