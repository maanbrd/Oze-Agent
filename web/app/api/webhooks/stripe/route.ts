import { NextResponse } from "next/server";
import type Stripe from "stripe";
import { forwardStripeEventToFastApi } from "@/lib/billing/stripe-events";
import { envValue, getStripe } from "@/lib/stripe/server";

export const runtime = "nodejs";

const FORWARDED_EVENTS = new Set([
  "checkout.session.completed",
  "checkout.session.async_payment_succeeded",
  "invoice.payment_succeeded",
  "invoice.payment_failed",
  "customer.subscription.updated",
  "customer.subscription.deleted",
]);

function requireWebhookEnv() {
  const webhookSecret = envValue("STRIPE_WEBHOOK_SECRET");

  if (!webhookSecret) {
    throw new Error(
      "Missing STRIPE_WEBHOOK_SECRET",
    );
  }

  return {
    webhookSecret,
  };
}

function normalizeEvent(event: Stripe.Event) {
  return {
    id: event.id,
    type: event.type,
    created: event.created,
    livemode: event.livemode,
    object: event.data.object,
  };
}

export async function POST(request: Request) {
  let env: ReturnType<typeof requireWebhookEnv>;
  try {
    env = requireWebhookEnv();
  } catch (error) {
    console.error("Stripe webhook env error", error);
    return NextResponse.json({ error: "Webhook not configured" }, { status: 500 });
  }

  const rawBody = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "Missing Stripe signature" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(
      rawBody,
      signature,
      env.webhookSecret,
    );
  } catch (error) {
    console.error("Stripe signature verification failed", error);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (!FORWARDED_EVENTS.has(event.type)) {
    return NextResponse.json({ received: true, forwarded: false });
  }

  try {
    await forwardStripeEventToFastApi(normalizeEvent(event));
  } catch (error) {
    console.error("FastAPI billing webhook request failed", error);
    return NextResponse.json(
      { error: "Billing write unavailable" },
      { status: 502 },
    );
  }

  return NextResponse.json({ received: true, forwarded: true });
}
