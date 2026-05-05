"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  createGoogleResources,
  generateTelegramCode,
  startGoogleOAuth,
  updateAccount,
} from "@/lib/api/onboarding";
import { getCurrentAccount } from "@/lib/api/account";
import {
  checkoutConfigErrorMessage,
  getStripe,
  requireStripeEnv,
  resolveStripePriceId,
} from "@/lib/stripe/server";
import { trustedExternalUrl } from "@/lib/routes";

type BillingPlan = "monthly" | "yearly";

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

function firstHeaderValue(value: string | null) {
  return value?.split(",")[0]?.trim() ?? "";
}

function isLocalhost(hostname: string) {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
}

function isTrustedReturnHost(hostname: string, fallbackAppUrl: string | null) {
  if (isLocalhost(hostname) || hostname.endsWith(".vercel.app")) return true;
  if (!fallbackAppUrl) return false;

  try {
    return hostname === new URL(fallbackAppUrl).hostname;
  } catch {
    return false;
  }
}

async function resolveCheckoutReturnBaseUrl(fallbackAppUrl: string | null) {
  const requestHeaders = await headers();
  const host = firstHeaderValue(
    requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host"),
  );

  if (!host) {
    if (fallbackAppUrl) return fallbackAppUrl;
    throw new Error("Missing request host and NEXT_PUBLIC_APP_URL");
  }

  const protocolHeader = firstHeaderValue(requestHeaders.get("x-forwarded-proto"));
  const candidateProtocol =
    protocolHeader === "http" && (host.startsWith("localhost") || host.startsWith("127.0.0.1"))
      ? "http"
      : "https";

  const candidateUrl = new URL(`${candidateProtocol}://${host}`);
  if (!isTrustedReturnHost(candidateUrl.hostname, fallbackAppUrl)) {
    if (fallbackAppUrl) return fallbackAppUrl;
    throw new Error(`Untrusted checkout return host: ${candidateUrl.hostname}`);
  }

  return candidateUrl.origin.replace(/\/$/, "");
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
    const returnBaseUrl = await resolveCheckoutReturnBaseUrl(appUrl);
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
        source: "web_onboarding",
      },
      subscription_data: {
        metadata: {
          auth_user_id: account.profile.auth_user_id,
          user_id: account.profile.id,
          plan,
          source: "web_onboarding",
        },
      },
      success_url: `${returnBaseUrl}/onboarding/sukces?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${returnBaseUrl}/onboarding/anulowano`,
    });

    checkoutUrl = session.url;
  } catch (error) {
    console.error("createCheckoutSession failed", error);
    redirect(
      encoded(
        "/onboarding/platnosc",
        checkoutConfigErrorMessage(error),
      ),
    );
  }

  if (!checkoutUrl) {
    redirect(encoded("/onboarding/platnosc", "Stripe nie zwrócił linku."));
  }

  const trustedCheckoutUrl = trustedExternalUrl(checkoutUrl, [
    "https://checkout.stripe.com",
  ]);
  if (!trustedCheckoutUrl) {
    redirect(
      encoded(
        "/onboarding/platnosc",
        "Stripe zwrócił nieoczekiwany adres checkoutu.",
      ),
    );
  }

  redirect(trustedCheckoutUrl);
}

export async function startGoogleOAuthAction() {
  let url: string;
  try {
    url = await startGoogleOAuth();
  } catch (error) {
    console.error("startGoogleOAuthAction failed", error);
    redirect(
      encoded(
        "/onboarding/google",
        "Nie udało się uruchomić autoryzacji Google. Spróbuj ponownie.",
      ),
    );
  }
  const trustedGoogleUrl = trustedExternalUrl(url, [
    "https://accounts.google.com",
  ]);
  if (!trustedGoogleUrl) {
    redirect(
      encoded(
        "/onboarding/google",
        "Google zwrócił nieoczekiwany adres autoryzacji.",
      ),
    );
  }

  redirect(trustedGoogleUrl);
}

export async function createGoogleResourcesAction(formData: FormData) {
  try {
    await createGoogleResources({
      sheetsName: String(formData.get("sheetsName") ?? ""),
      calendarName: String(formData.get("calendarName") ?? ""),
    });
  } catch (error) {
    console.error("createGoogleResourcesAction failed", error);
    redirect(
      encoded(
        "/onboarding/zasoby",
        "Nie udało się utworzyć zasobów Google. Sprawdź połączenie Google i spróbuj ponownie.",
      ),
    );
  }
  redirect("/onboarding/telegram");
}

export async function generateTelegramCodeAction() {
  try {
    await generateTelegramCode();
  } catch (error) {
    console.error("generateTelegramCodeAction failed", error);
    redirect(
      encoded(
        "/onboarding/telegram",
        "Nie udało się wygenerować kodu Telegram. Dokończ płatność i Google, a potem spróbuj ponownie.",
      ),
    );
  }
  redirect("/onboarding/telegram");
}

export async function updateAccountAction(formData: FormData) {
  try {
    await updateAccount({
      name: String(formData.get("name") ?? ""),
      phone: String(formData.get("phone") ?? ""),
    });
  } catch (error) {
    console.error("updateAccountAction failed", error);
    redirect(encoded("/ustawienia", "Nie udało się zapisać ustawień konta."));
  }
  redirect("/ustawienia?saved=1");
}
