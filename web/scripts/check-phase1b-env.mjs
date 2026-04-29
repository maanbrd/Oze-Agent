const VALID_SCOPES = new Set(["local", "staging"]);

function argValue(name) {
  const prefix = `${name}=`;
  const match = process.argv.slice(2).find((arg) => arg.startsWith(prefix));
  return match ? match.slice(prefix.length) : null;
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
  const report = phase1bEnvReport(scope());
  printReport(report);
  if (report.missing.length || report.errors.length) {
    process.exit(1);
  }
  console.log("Phase 1B web env OK");
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
