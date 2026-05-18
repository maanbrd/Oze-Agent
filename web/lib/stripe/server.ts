import "server-only";

import Stripe from "stripe";

let stripeClient: Stripe | null = null;

export const STRIPE_PRICE_LOOKUP_KEYS = {
  monthly: "agent_oze_monthly_399",
} as const;

const EXPECTED_MONTHLY_UNIT_AMOUNT = 39900;
const EXPECTED_MONTHLY_CURRENCY = "pln";
const EXPECTED_MONTHLY_INTERVAL = "month";

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

async function findStripePrice(priceRef: string) {
  const cleanPriceRef = priceRef.trim();
  if (!cleanPriceRef) {
    throw new Error("Missing Stripe price reference");
  }

  if (cleanPriceRef.startsWith("price_")) {
    return getStripe().prices.retrieve(cleanPriceRef);
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

  return price;
}

function isExpectedMonthlyPrice(price: Stripe.Price) {
  return (
    price.unit_amount === EXPECTED_MONTHLY_UNIT_AMOUNT &&
    price.currency === EXPECTED_MONTHLY_CURRENCY &&
    price.recurring?.interval === EXPECTED_MONTHLY_INTERVAL
  );
}

function assertExpectedMonthlyPrice(price: Stripe.Price) {
  if (isExpectedMonthlyPrice(price)) return;

  throw new Error(
    "Resolved Stripe price does not match Agent OZE monthly 399 PLN",
  );
}

export async function resolveStripePriceId(priceRef: string) {
  return (await findStripePrice(priceRef)).id;
}

export async function resolveStripeMonthlyPriceId(priceRef: string) {
  const price = await findStripePrice(priceRef);
  if (isExpectedMonthlyPrice(price)) {
    return price.id;
  }

  if (priceRef.trim() !== STRIPE_PRICE_LOOKUP_KEYS.monthly) {
    const fallbackPrice = await findStripePrice(STRIPE_PRICE_LOOKUP_KEYS.monthly);
    assertExpectedMonthlyPrice(fallbackPrice);
    return fallbackPrice.id;
  }

  assertExpectedMonthlyPrice(price);
  return price.id;
}

export function checkoutConfigErrorMessage(error: unknown) {
  const message = error instanceof Error ? error.message : "";

  if (message.includes("Missing STRIPE_SECRET_KEY")) {
    return "Płatność nie jest jeszcze skonfigurowana. Wróć później albo skontaktuj się z obsługą Agent OZE.";
  }

  if (message.includes("Missing Stripe price reference")) {
    return "Plan płatności nie jest jeszcze skonfigurowany. Wróć później albo skontaktuj się z obsługą Agent OZE.";
  }

  if (message.includes("No active Stripe price found for lookup key")) {
    return "Nie udało się znaleźć aktywnego planu płatności. Wróć później albo skontaktuj się z obsługą Agent OZE.";
  }

  if (message.includes("Resolved Stripe price does not match Agent OZE monthly 399 PLN")) {
    return "Plan płatności ma niepoprawną kwotę. Wróć później albo skontaktuj się z obsługą Agent OZE.";
  }

  return "Nie udało się uruchomić płatności. Sprawdź konfigurację Stripe.";
}
