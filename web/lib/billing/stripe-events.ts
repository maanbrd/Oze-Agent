import "server-only";

import { createHmac } from "crypto";
import { normalizeFastApiBaseUrl } from "@/lib/api/base-url";
import { envValue } from "@/lib/stripe/server";

export type NormalizedStripeEvent = {
  id: string;
  type: string;
  created: number;
  livemode: boolean;
  object: unknown;
};

const FASTAPI_FORWARD_TIMEOUT_MS = 8000;

export function requireBillingForwardEnv() {
  const billingSecret = envValue("BILLING_INTERNAL_SECRET");
  const fastapiBaseUrl = envValue("FASTAPI_INTERNAL_BASE_URL");

  if (!billingSecret || !fastapiBaseUrl) {
    throw new Error("Missing BILLING_INTERNAL_SECRET or FASTAPI_INTERNAL_BASE_URL");
  }

  return {
    billingSecret,
    fastapiBaseUrl: normalizeFastApiBaseUrl(fastapiBaseUrl),
  };
}

function signInternalBody(body: string, timestamp: string, secret: string) {
  return createHmac("sha256", secret)
    .update(`${timestamp}.${body}`)
    .digest("hex");
}

async function postStripeEvent(
  url: string,
  body: string,
  headers: HeadersInit,
) {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    FASTAPI_FORWARD_TIMEOUT_MS,
  );
  try {
    return await fetch(url, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export async function forwardStripeEventToFastApi(event: NormalizedStripeEvent) {
  const env = requireBillingForwardEnv();
  const body = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const signature = signInternalBody(body, timestamp, env.billingSecret);

  const response = await postStripeEvent(
    `${env.fastapiBaseUrl}/internal/billing/stripe-event`,
    body,
    {
      "Content-Type": "application/json",
      "X-OZE-Timestamp": timestamp,
      "X-OZE-Signature": `sha256=${signature}`,
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`FastAPI billing webhook failed ${response.status}: ${errorText}`);
  }

  return response;
}
