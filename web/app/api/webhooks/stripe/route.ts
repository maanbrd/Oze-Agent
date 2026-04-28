import { createHmac } from "crypto";
import { NextResponse } from "next/server";
import type Stripe from "stripe";
import { getStripe } from "@/lib/stripe/server";

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
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  const billingSecret = process.env.BILLING_INTERNAL_SECRET;
  const fastapiBaseUrl = process.env.FASTAPI_INTERNAL_BASE_URL;

  if (!webhookSecret || !billingSecret || !fastapiBaseUrl) {
    throw new Error(
      "Missing STRIPE_WEBHOOK_SECRET, BILLING_INTERNAL_SECRET, or FASTAPI_INTERNAL_BASE_URL",
    );
  }

  return {
    webhookSecret,
    billingSecret,
    fastapiBaseUrl: fastapiBaseUrl.replace(/\/$/, ""),
  };
}

function signInternalBody(body: string, timestamp: string, secret: string) {
  return createHmac("sha256", secret)
    .update(`${timestamp}.${body}`)
    .digest("hex");
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

  if (event.livemode) {
    console.error("Live Stripe webhook rejected in Phase 0C", event.id);
    return NextResponse.json(
      { error: "Live Stripe events are disabled in Phase 0C" },
      { status: 400 },
    );
  }

  if (!FORWARDED_EVENTS.has(event.type)) {
    return NextResponse.json({ received: true, forwarded: false });
  }

  const body = JSON.stringify(normalizeEvent(event));
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const internalSignature = signInternalBody(
    body,
    timestamp,
    env.billingSecret,
  );

  const response = await fetch(
    `${env.fastapiBaseUrl}/internal/billing/stripe-event`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-OZE-Timestamp": timestamp,
        "X-OZE-Signature": `sha256=${internalSignature}`,
      },
      body,
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("FastAPI billing webhook failed", response.status, errorText);
    return NextResponse.json(
      { error: "Billing write failed" },
      { status: 502 },
    );
  }

  return NextResponse.json({ received: true, forwarded: true });
}
