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
    return "Lokalny env nie zawiera aktywnego STRIPE_SECRET_KEY. Jeśli Stripe działał wcześniej, web/.env.local mógł zostać nadpisany. Przywróć klucz z backupu, Stripe Dashboard albo Vercel env.";
  }

  if (message.includes("Missing Stripe price reference")) {
    return "Lokalny env Stripe nie zawiera ceny ani lookup key dla planu miesięcznego. Przywróć STRIPE_PRICE_MONTHLY z backupu albo Vercel env.";
  }

  if (message.includes("No active Stripe price found for lookup key")) {
    return "Nie znaleziono aktywnej ceny Stripe dla zapisanego lookup key. Przywróć właściwe STRIPE_PRICE_MONTHLY albo sprawdź ceny w Stripe.";
  }

  return "Nie udało się uruchomić płatności. Sprawdź konfigurację Stripe.";
}
