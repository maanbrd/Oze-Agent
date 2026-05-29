"use client";

import { useLinkStatus } from "next/link";
import { useEffect } from "react";
import { useNavigationProgress } from "./navigation-bar";

export function LinkStatusWatcher() {
  const status = useLinkStatus();
  const { show, hide } = useNavigationProgress();

  useEffect(() => {
    if (status.pending) {
      show();
    } else {
      hide();
    }
  }, [status.pending, show, hide]);

  return null;
}
