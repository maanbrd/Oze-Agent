import "server-only";

import Stripe from "stripe";

let stripeClient: Stripe | null = null;

export const STRIPE_PRICE_LOOKUP_KEYS = {
  activation: "agent_oze_activation_199",
  monthly: "agent_oze_monthly_49",
  yearly: "agent_oze_yearly_350",
} as const;

export function getStripe() {
  if (!stripeClient) {
    const secretKey = process.env.STRIPE_SECRET_KEY;
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
  const activationPrice =
    process.env.STRIPE_PRICE_ACTIVATION ?? STRIPE_PRICE_LOOKUP_KEYS.activation;
  const monthlyPrice =
    process.env.STRIPE_PRICE_MONTHLY ?? STRIPE_PRICE_LOOKUP_KEYS.monthly;
  const yearlyPrice =
    process.env.STRIPE_PRICE_YEARLY ?? STRIPE_PRICE_LOOKUP_KEYS.yearly;
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;

  if (!appUrl) {
    throw new Error("Missing NEXT_PUBLIC_APP_URL");
  }

  return {
    activationPrice,
    monthlyPrice,
    yearlyPrice,
    appUrl: appUrl.replace(/\/$/, ""),
  };
}

export async function resolveStripePriceId(priceRef: string) {
  if (priceRef.startsWith("price_")) {
    return priceRef;
  }

  const prices = await getStripe().prices.list({
    active: true,
    lookup_keys: [priceRef],
    limit: 1,
  });

  const price = prices.data[0];
  if (!price) {
    throw new Error(`No active Stripe price found for lookup key: ${priceRef}`);
  }

  return price.id;
}
