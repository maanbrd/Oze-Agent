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

type StripeObjectWithSubscription = Stripe.Event.Data.Object & {
  object?: string;
  subscription?: string | Stripe.Subscription | null;
  subscription_details?: StripeSubscriptionDetails;
};

type StripeSubscriptionDetails = {
  id: string;
  status: Stripe.Subscription.Status;
  current_period_start: unknown;
  current_period_end: unknown;
  cancel_at_period_end: unknown;
  livemode: boolean;
};

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

function compactSubscriptionDetails(
  subscription: Stripe.Subscription,
): StripeSubscriptionDetails {
  const raw = subscription as unknown as Record<string, unknown>;
  return {
    id: subscription.id,
    status: subscription.status,
    current_period_start: raw.current_period_start,
    current_period_end: raw.current_period_end,
    cancel_at_period_end: raw.cancel_at_period_end,
    livemode: subscription.livemode,
  };
}

function subscriptionIdFromObject(object: StripeObjectWithSubscription) {
  const subscription = object.subscription;
  if (!subscription) return null;
  if (typeof subscription === "string") return subscription;
  return subscription.id;
}

async function enrichStripeObject(
  object: Stripe.Event.Data.Object,
): Promise<StripeObjectWithSubscription> {
  const stripeObject = object as StripeObjectWithSubscription;
  if (stripeObject.object === "subscription") {
    const subscription = stripeObject as unknown as Stripe.Subscription;
    return {
      ...stripeObject,
      subscription_details: compactSubscriptionDetails(subscription),
    };
  }

  const subscriptionId = subscriptionIdFromObject(stripeObject);
  if (!subscriptionId) return stripeObject;

  const subscription = await getStripe().subscriptions.retrieve(subscriptionId);
  return {
    ...stripeObject,
    subscription_details: compactSubscriptionDetails(subscription),
  };
}

async function normalizeEvent(event: Stripe.Event) {
  return {
    id: event.id,
    type: event.type,
    created: event.created,
    livemode: event.livemode,
    object: await enrichStripeObject(event.data.object),
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
    await forwardStripeEventToFastApi(await normalizeEvent(event));
  } catch (error) {
    console.error("FastAPI billing webhook request failed", error);
    return NextResponse.json(
      { error: "Billing write unavailable" },
      { status: 502 },
    );
  }

  return NextResponse.json({ received: true, forwarded: true });
}
