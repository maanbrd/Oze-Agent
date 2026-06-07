// Security response headers for Agent-OZE web (Cloudflare "SaaS Top 10" audit,
// mechanism #8). Pure + dependency-free so next.config.ts can import it and
// node:test can unit-test it without node_modules.
//
// Rollout is deliberately staged via env flags so we never break production:
//   * CSP ships as Content-Security-Policy-REPORT-ONLY by default. Set
//     CSP_ENFORCE=true only after the browser console / report endpoint shows
//     no violations on a real deploy.
//   * HSTS starts at 1 day. Raise HSTS_MAX_AGE (e.g. 15552000 = 180d) and set
//     HSTS_INCLUDE_SUBDOMAINS=true once every agent-oze.pl subdomain is HTTPS,
//     then HSTS_PRELOAD=true before submitting to the preload list.
//
// CSP notes: 'unsafe-inline' on script/style is required by Next.js without
// nonces (nonces force dynamic rendering — see content-security-policy docs).
// The lists below cover what the app talks to; tune from Report-Only findings.

export const SCRIPT_SRC = [
  "'self'",
  "'unsafe-inline'", // required by Next.js without per-request nonces
  "https://js.stripe.com",
  "https://va.vercel-scripts.com", // Vercel Analytics (no-op if unused)
];

export const CONNECT_SRC = [
  "'self'",
  "https://*.supabase.co",
  "wss://*.supabase.co", // Supabase realtime, if used
  "https://*.up.railway.app", // FastAPI backend if called from the browser
  "https://*.vercel-insights.com", // Vercel Speed Insights (no-op if unused)
];

export const FORM_ACTION = [
  "'self'",
  "https://checkout.stripe.com", // Stripe Checkout redirect
  "https://accounts.google.com", // Google OAuth redirect
];

export function buildCsp() {
  return [
    "default-src 'self'",
    `script-src ${SCRIPT_SRC.join(" ")}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data:",
    `connect-src ${CONNECT_SRC.join(" ")}`,
    "frame-src https://*.stripe.com",
    "object-src 'none'",
    "base-uri 'self'",
    `form-action ${FORM_ACTION.join(" ")}`,
    "frame-ancestors 'none'",
    "upgrade-insecure-requests",
  ].join("; ");
}

export function buildHsts({
  maxAge = Number(process.env.HSTS_MAX_AGE || 86400), // 1 day default (staged)
  includeSubDomains = process.env.HSTS_INCLUDE_SUBDOMAINS === "true",
  preload = process.env.HSTS_PRELOAD === "true",
} = {}) {
  let value = `max-age=${maxAge}`;
  if (includeSubDomains) value += "; includeSubDomains";
  if (preload) value += "; preload";
  return value;
}

export function buildSecurityHeaders({
  enforceCsp = process.env.CSP_ENFORCE === "true",
  hsts = buildHsts(),
} = {}) {
  const cspKey = enforceCsp
    ? "Content-Security-Policy"
    : "Content-Security-Policy-Report-Only";

  return [
    { key: cspKey, value: buildCsp() },
    { key: "Strict-Transport-Security", value: hsts },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    {
      key: "Permissions-Policy",
      value: "geolocation=(), microphone=(), camera=()",
    },
  ];
}
