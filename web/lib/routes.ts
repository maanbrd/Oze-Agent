export function safeLocalPath(
  value: string | null | undefined,
  fallback = "/dashboard",
) {
  if (!value) return fallback;
  if (/[\u0000-\u001F\u007F\\]/.test(value)) return fallback;
  if (!value.startsWith("/") || value.startsWith("//")) return fallback;

  try {
    const parsed = new URL(value, "https://agent-oze.local");
    if (parsed.origin !== "https://agent-oze.local") return fallback;
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}

export function trustedExternalUrl(
  value: string | null | undefined,
  allowedOrigins: readonly string[],
) {
  if (!value) return null;

  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "https:") return null;
    if (!allowedOrigins.includes(parsed.origin)) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}
