"use server";

import { redirect } from "next/navigation";
import { getCurrentAccount } from "@/lib/api/account";
import {
  getStripe,
  requireStripeEnv,
  resolveStripePriceId,
} from "@/lib/stripe/server";

type BillingPlan = "monthly" | "yearly";

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

function planFromForm(formData: FormData): BillingPlan {
  const plan = String(formData.get("plan") ?? "");
  return plan === "yearly" ? "yearly" : "monthly";
}

export async function createCheckoutSession(formData: FormData) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect("/login?next=/onboarding/platnosc");
  }

  if (!account.profile) {
    redirect(
      encoded(
        "/onboarding/platnosc",
        account.error ?? "Nie znaleziono profilu konta.",
      ),
    );
  }

  const plan = planFromForm(formData);
  let checkoutUrl: string | null = null;

  try {
    const { activationPrice, monthlyPrice, yearlyPrice, appUrl } =
      requireStripeEnv();
    const stripe = getStripe();
    const recurringPriceRef = plan === "yearly" ? yearlyPrice : monthlyPrice;
    const [recurringPriceId, activationPriceId] = await Promise.all([
      resolveStripePriceId(recurringPriceRef),
      resolveStripePriceId(activationPrice),
    ]);

    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer_email: account.email ?? account.profile.email ?? undefined,
      client_reference_id: account.profile.id,
      line_items: [
        { price: recurringPriceId, quantity: 1 },
        { price: activationPriceId, quantity: 1 },
      ],
      metadata: {
        auth_user_id: account.profile.auth_user_id,
        user_id: account.profile.id,
        plan,
        source: "web_onboarding_0c",
      },
      subscription_data: {
        metadata: {
          auth_user_id: account.profile.auth_user_id,
          user_id: account.profile.id,
          plan,
          source: "web_onboarding_0c",
        },
      },
      success_url: `${appUrl}/onboarding/sukces?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${appUrl}/onboarding/anulowano`,
    });

    checkoutUrl = session.url;
  } catch (error) {
    console.error("createCheckoutSession failed", error);
    redirect(
      encoded(
        "/onboarding/platnosc",
        "Nie udało się uruchomić płatności. Sprawdź konfigurację Stripe.",
      ),
    );
  }

  if (!checkoutUrl) {
    redirect(encoded("/onboarding/platnosc", "Stripe nie zwrócił linku."));
  }

  redirect(checkoutUrl);
}
