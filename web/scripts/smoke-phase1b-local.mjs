import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const DEFAULT_BASE_URL = "http://127.0.0.1:3000";
const DEFAULT_TIMEOUT_MS = 8000;

function argValue(name) {
  const prefix = `${name}=`;
  const match = process.argv.slice(2).find((arg) => arg.startsWith(prefix));
  return match ? match.slice(prefix.length) : null;
}

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function walk(dir) {
  const entries = readdirSync(join(root, dir));
  return entries.flatMap((entry) => {
    const relative = join(dir, entry);
    const absolute = join(root, relative);
    if (statSync(absolute).isDirectory()) return walk(relative);
    return relative;
  });
}

function withTrailingSlashless(url) {
  return url.replace(/\/$/, "");
}

function locationPath(location, baseUrl) {
  if (!location) return "";
  const parsed = new URL(location, baseUrl);
  return `${parsed.pathname}${parsed.search}`;
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs);
  try {
    return await fetch(url, {
      redirect: "manual",
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

class SmokeRunner {
  constructor({ baseUrl, timeoutMs }) {
    this.baseUrl = baseUrl;
    this.timeoutMs = timeoutMs;
    this.results = [];
  }

  async check(name, fn) {
    try {
      await fn();
      this.results.push({ name, ok: true });
    } catch (error) {
      this.results.push({
        name,
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  assert(condition, message) {
    if (!condition) throw new Error(message);
  }

  async request(path) {
    const url = new URL(path, this.baseUrl);
    return fetchWithTimeout(url, { timeoutMs: this.timeoutMs });
  }

  async expectHtml(path, pattern) {
    const response = await this.request(path);
    const text = await response.text();
    this.assert(
      response.status === 200,
      `${path} returned ${response.status}, expected 200.`,
    );
    this.assert(pattern.test(text), `${path} did not include ${pattern}.`);
  }

  async expectRedirect(path, expectedLocation) {
    const response = await this.request(path);
    const actualLocation = locationPath(
      response.headers.get("location"),
      this.baseUrl,
    );
    this.assert(
      [302, 303, 307, 308].includes(response.status),
      `${path} returned ${response.status}, expected redirect.`,
    );
    this.assert(
      actualLocation === expectedLocation,
      `${path} redirected to ${actualLocation || "empty location"}, expected ${expectedLocation}.`,
    );
  }

  print() {
    console.log(`Phase 1B local smoke target: ${this.baseUrl}`);
    for (const result of this.results) {
      if (result.ok) {
        console.log(`OK ${result.name}`);
      } else {
        console.log(`FAIL ${result.name}: ${result.error}`);
      }
    }
  }

  get failed() {
    return this.results.filter((result) => !result.ok);
  }
}

async function run() {
  const baseUrl = withTrailingSlashless(
    argValue("--base-url") ?? process.env.PHASE1B_LOCAL_BASE_URL ?? DEFAULT_BASE_URL,
  );
  const timeoutMs = Number(argValue("--timeout-ms") ?? DEFAULT_TIMEOUT_MS);
  const smoke = new SmokeRunner({ baseUrl, timeoutMs });

  await smoke.check("health route returns JSON", async () => {
    const response = await smoke.request("/healthz");
    smoke.assert(response.status === 200, `/healthz returned ${response.status}.`);
    const data = await response.json();
    smoke.assert(data.status === "ok", "/healthz did not return status ok.");
    smoke.assert(
      data.service === "agent-oze-web",
      "/healthz did not identify the web service.",
    );
  });

  await smoke.check("public landing renders", async () => {
    await smoke.expectHtml("/", /Agent-OZE|OZE Agent/i);
  });

  await smoke.check("login page renders", async () => {
    await smoke.expectHtml("/login", /Logowanie/);
  });

  await smoke.check("registration page renders", async () => {
    await smoke.expectHtml("/rejestracja", /Rejestracja/);
  });

  await smoke.check("dashboard redirects anonymous users", async () => {
    await smoke.expectRedirect("/dashboard", "/login?next=/dashboard");
  });

  await smoke.check("clients redirects anonymous users", async () => {
    await smoke.expectRedirect("/klienci", "/login?next=/dashboard");
  });

  await smoke.check("calendar redirects anonymous users", async () => {
    await smoke.expectRedirect("/kalendarz", "/login?next=/dashboard");
  });

  await smoke.check("payment step redirects anonymous users", async () => {
    await smoke.expectRedirect(
      "/onboarding/platnosc",
      "/login?next=/onboarding/platnosc",
    );
  });

  await smoke.check("onboarding gate is wired into app shell", async () => {
    smoke.assert(
      /OnboardingGate/.test(read("components/app-shell.tsx")),
      "App shell does not render OnboardingGate.",
    );
    smoke.assert(
      /getOnboardingStatus/.test(read("app/(app)/layout.tsx")),
      "Logged-in layout does not fetch onboarding status.",
    );
  });

  await smoke.check("CRM mutation forms are absent", async () => {
    const appFiles = walk("app").filter((file) => file.endsWith(".tsx"));
    const source = appFiles.map((file) => read(file)).join("\n");
    smoke.assert(
      !/action=\{.*addClient|action=\{.*updateClient|name="status"/s.test(source),
      "CRM mutation forms are present in app routes.",
    );
  });

  smoke.print();
  if (smoke.failed.length) {
    process.exit(1);
  }
}

run().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
