export function normalizeFastApiBaseUrl(value: string | null | undefined) {
  const trimmed = (value ?? "").trim();
  if (!trimmed || trimmed === `""` || trimmed === "''") return "";

  try {
    const url = new URL(trimmed);
    const path = url.pathname.replace(/\/+$/, "");
    if (path === "/api") {
      url.pathname = "/";
    }
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/$/, "");
  } catch {
    return trimmed.replace(/\/$/, "");
  }
}

export function fastApiBaseUrl() {
  return (
    normalizeFastApiBaseUrl(process.env.FASTAPI_INTERNAL_BASE_URL) ||
    normalizeFastApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL)
  );
}
