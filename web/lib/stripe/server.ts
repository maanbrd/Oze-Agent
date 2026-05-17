import "server-only";

import Stripe from "stripe";

let stripeClient: Stripe | null = null;

export const STRIPE_PRICE_LOOKUP_KEYS = {
  monthly: "agent_oze_monthly_399",
} as const;

export function envValue(name: string) {
  const value = process.env[name]?.trim();
  if (!value || value === `""` || value === "''") {
    return null;
  }

  return value;
}

export function getStripe() {
  if (!stripeClient) {
    const secretKey = envValue("STRIPE_SECRET_KEY");
    if (!secretKey) {
      throw new Error("Missing STRIPE_SECRET_KEY");
    }

    stripeClient = new Stripe(secretKey, {
      apiVersion: "2026-04-22.dahlia",
      typescript: true,
    });
  }

  return stripeClient;
}

export function requireStripeEnv() {
  const monthlyPrice =
    envValue("STRIPE_PRICE_MONTHLY") ?? STRIPE_PRICE_LOOKUP_KEYS.monthly;
  const appUrl = envValue("NEXT_PUBLIC_APP_URL")?.replace(/\/$/, "") ?? null;

  return {
    monthlyPrice,
    appUrl,
  };
}

export async function resolveStripePriceId(priceRef: string) {
  const cleanPriceRef = priceRef.trim();
  if (!cleanPriceRef) {
    throw new Error("Missing Stripe price reference");
  }

  if (cleanPriceRef.startsWith("price_")) {
    return cleanPriceRef;
  }

  const prices = await getStripe().prices.list({
    active: true,
    lookup_keys: [cleanPriceRef],
    limit: 1,
  });

  const price = prices.data[0];
  if (!price) {
    throw new Error(
      `No active Stripe price found for lookup key: ${cleanPriceRef}`,
    );
  }

  return price.id;
}

export function checkoutConfigErrorMessage(error: unknown) {
  const message = error instanceof Error ? error.message : "";

  if (message.includes("Missing STRIPE_SECRET_KEY")) {
    return "Płatność nie jest jeszcze skonfigurowana. Wróć później albo skontaktuj się z obsługą Agent-OZE.";
  }

  if (message.includes("Missing Stripe price reference")) {
    return "Plan płatności nie jest jeszcze skonfigurowany. Wróć później albo skontaktuj się z obsługą Agent-OZE.";
  }

  if (message.includes("No active Stripe price found for lookup key")) {
    return "Nie udało się znaleźć aktywnego planu płatności. Wróć później albo skontaktuj się z obsługą Agent-OZE.";
  }

  return "Nie udało się uruchomić płatności. Sprawdź konfigurację Stripe.";
}
