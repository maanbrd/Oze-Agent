import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const layoutSrc = readSource("../app/layout.tsx");

test("app/layout.tsx wraps children with NavigationProgressProvider", () => {
  assert.match(layoutSrc, /NavigationProgressProvider/);
});

test("LinkStatusWatcher exists and uses useLinkStatus from next/link", () => {
  const watcherSrc = readSource("../components/ui/use-link-status-watcher.tsx");
  assert.match(watcherSrc, /useLinkStatus/);
  assert.match(watcherSrc, /useNavigationProgress/);
});
