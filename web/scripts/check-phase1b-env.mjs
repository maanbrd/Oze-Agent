import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const VALID_SCOPES = new Set(["local", "staging"]);
const DEFAULT_ENV_FILES = [".env.local", ".env"];

function argValue(name) {
  const prefix = `${name}=`;
  const match = process.argv.slice(2).find((arg) => arg.startsWith(prefix));
  return match ? match.slice(prefix.length) : null;
}

function unquote(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseEnvFile(path) {
  const values = new Map();
  const source = readFileSync(path, "utf8");

  for (const rawLine of source.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    const normalized = line.startsWith("export ") ? line.slice(7).trim() : line;
    const separator = normalized.indexOf("=");
    if (separator <= 0) continue;

    const name = normalized.slice(0, separator).trim();
    const value = normalized.slice(separator + 1);
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
      values.set(name, unquote(value));
    }
  }

  return values;
}

function loadEnvFile(path) {
  const resolved = resolve(path);
  for (const [name, value] of parseEnvFile(resolved)) {
    if (process.env[name] === undefined) {
      process.env[name] = value;
    }
  }
  return resolved;
}

function loadEnvFiles() {
  const explicitPath = argValue("--env-file");
  if (explicitPath) {
    return [loadEnvFile(explicitPath)];
  }

  return DEFAULT_ENV_FILES.filter((path) => existsSync(path)).map(loadEnvFile);
}

function scope() {
  const value = argValue("--scope") ?? process.env.PHASE1B_ENV_SCOPE ?? "local";
  if (!VALID_SCOPES.has(value)) {
    throw new Error("Use --scope=local or --scope=staging.");
  }
  return value;
}

function present(name) {
  return Boolean((process.env[name] ?? "").trim());
}

function envValue(name) {
  return (process.env[name] ?? "").trim();
}

function parseUrl(name, errors) {
  const value = envValue(name);
  if (!value) return null;
  try {
    return new URL(value);
  } catch {
    errors.push(`${name} must be a valid URL.`);
    return null;
  }
}

function validateUrlConfig(selectedScope, errors) {
  for (const name of [
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_API_BASE_URL",
    "NEXT_PUBLIC_APP_URL",
    "FASTAPI_INTERNAL_BASE_URL",
  ]) {
    const url = parseUrl(name, errors);
    if (!url) continue;

    if (!["http:", "https:"].includes(url.protocol)) {
      errors.push(`${name} must use http or https.`);
    }
    if (selectedScope === "staging" && url.protocol !== "https:") {
      errors.push(`${name} must use https in staging.`);
    }
  }
}

function phase1bEnvReport(selectedScope) {
  const required = [
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    "NEXT_PUBLIC_API_BASE_URL",
    "NEXT_PUBLIC_APP_URL",
    "FASTAPI_INTERNAL_BASE_URL",
    "BILLING_INTERNAL_SECRET",
    "STRIPE_SECRET_KEY",
    "STRIPE_PRICE_ACTIVATION",
    "STRIPE_PRICE_MONTHLY",
    "STRIPE_PRICE_YEARLY",
  ];

  if (selectedScope === "staging") {
    required.push("STRIPE_WEBHOOK_SECRET");
  }

  const missing = required.filter((name) => !present(name));
  const errors = [];
  const warnings = [];
  const stripeKey = (process.env.STRIPE_SECRET_KEY ?? "").trim();

  if (present("SUPABASE_SERVICE_KEY")) {
    errors.push(
      "SUPABASE_SERVICE_KEY must not be configured in the web/Vercel environment.",
    );
  }

  validateUrlConfig(selectedScope, errors);

  if (stripeKey.startsWith("sk_live_")) {
    errors.push("STRIPE_SECRET_KEY is live mode. Phase 1B must use test mode.");
  } else if (stripeKey && !stripeKey.startsWith("sk_test_")) {
    warnings.push("STRIPE_SECRET_KEY does not look like a Stripe test key.");
  }

  if (selectedScope === "local" && !present("STRIPE_WEBHOOK_SECRET")) {
    warnings.push(
      "STRIPE_WEBHOOK_SECRET is not required for local checks; full webhook smoke runs in staging.",
    );
  }

  return { errors, missing, scope: selectedScope, warnings };
}

function printReport(report) {
  console.log(`Phase 1B web env scope: ${report.scope}`);
  if (report.loadedEnvFiles.length) {
    console.log(`Loaded env file(s): ${report.loadedEnvFiles.join(", ")}`);
  }
  if (report.missing.length) {
    console.log(`Missing: ${report.missing.join(", ")}`);
  }
  for (const warning of report.warnings) {
    console.log(`Warning: ${warning}`);
  }
  for (const error of report.errors) {
    console.log(`Error: ${error}`);
  }
}

try {
  const loadedEnvFiles = loadEnvFiles();
  const report = phase1bEnvReport(scope());
  report.loadedEnvFiles = loadedEnvFiles;
  printReport(report);
  if (report.missing.length || report.errors.length) {
    process.exit(1);
  }
  console.log("Phase 1B web env OK");
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
