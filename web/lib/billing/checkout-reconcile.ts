import "server-only";

import type Stripe from "stripe";
import { getCurrentAccount, type AccountProfile } from "@/lib/api/account";
import { getStripe } from "@/lib/stripe/server";
import { forwardStripeEventToFastApi } from "@/lib/billing/stripe-events";

const CHECKOUT_SESSION_ID_PATTERN = /^cs_(test|live)_[A-Za-z0-9]+$/;

function cleanSessionId(value: string | null | undefined) {
  const sessionId = value?.trim();
  return sessionId && CHECKOUT_SESSION_ID_PATTERN.test(sessionId)
    ? sessionId
    : null;
}

export function isPaidCheckoutSessionForAccount(
  session: Stripe.Checkout.Session,
  profile: AccountProfile,
) {
  const ownedByProfile =
    session.client_reference_id === profile.id ||
    session.metadata?.user_id === profile.id;
  const authMatches =
    !session.metadata?.auth_user_id ||
    session.metadata?.auth_user_id === profile.auth_user_id;

  return (
    session.mode === "subscription" &&
    session.status === "complete" &&
    session.payment_status === "paid" &&
    ownedByProfile &&
    authMatches
  );
}

export async function reconcileCheckoutSession(
  rawSessionId: string | null | undefined,
) {
  const sessionId = cleanSessionId(rawSessionId);
  if (!sessionId) return false;

  const account = await getCurrentAccount();
  if (!account.authenticated || !account.profile) return false;

  const stripe = getStripe();
  const session = await stripe.checkout.sessions.retrieve(sessionId);

  if (!isPaidCheckoutSessionForAccount(session, account.profile)) {
    return false;
  }

  await forwardStripeEventToFastApi({
    id: `evt_reconcile_${session.id}`,
    type: "checkout.session.completed",
    created: session.created,
    livemode: session.livemode,
    object: session,
  });

  return true;
}
