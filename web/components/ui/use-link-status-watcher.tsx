"use client";

import { useLinkStatus } from "next/link";
import { useEffect } from "react";
import { useNavigationProgress } from "./navigation-bar";

/**
 * Render-nothing client component that drives the global navigation progress
 * bar from a Next.js `<Link>` navigation.
 *
 * MUST be mounted as a descendant of a `<Link>` element. `useLinkStatus()`
 * only returns `pending: true` while the enclosing Link is navigating — used
 * anywhere else it is a silent no-op (the bar will never appear).
 *
 * Mount one instance per Link that should trigger the bar, e.g.:
 *   <Link href="/foo"><LinkStatusWatcher />Foo</Link>
 */
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
