import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { trustedExternalUrl } from "@/lib/routes";
import {
  checkoutConfigErrorMessage,
  getStripe,
  requireStripeEnv,
  resolveStripeMonthlyPriceId,
} from "@/lib/stripe/server";

export const dynamic = "force-dynamic";
const BILLING_PLAN = "monthly";

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

function resolveCheckoutReturnBaseUrl(
  request: Request,
  fallbackAppUrl: string | null,
) {
  const host = firstHeaderValue(
    request.headers.get("x-forwarded-host") ?? request.headers.get("host"),
  );

  if (!host) {
    if (fallbackAppUrl) return fallbackAppUrl;
    throw new Error("Missing request host and NEXT_PUBLIC_APP_URL");
  }

  const protocolHeader = firstHeaderValue(request.headers.get("x-forwarded-proto"));
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

function localRedirect(request: Request, path: string) {
  return NextResponse.redirect(new URL(path, request.url), { status: 303 });
}

async function handleCheckout(request: Request) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    return localRedirect(request, "/login?next=/onboarding/platnosc");
  }

  if (!account.profile) {
    return localRedirect(
      request,
      encoded(
        "/onboarding/platnosc",
        account.error ?? "Nie znaleziono profilu konta.",
      ),
    );
  }

  let checkoutUrl: string | null = null;

  try {
    const { monthlyPrice, appUrl } = requireStripeEnv();
    const returnBaseUrl = resolveCheckoutReturnBaseUrl(request, appUrl);
    const stripe = getStripe();
    const recurringPriceId = await resolveStripeMonthlyPriceId(monthlyPrice);

    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      payment_method_types: ["card"],
      payment_method_collection: "always",
      customer_email: account.email ?? account.profile.email ?? undefined,
      client_reference_id: account.profile.id,
      line_items: [{ price: recurringPriceId, quantity: 1 }],
      metadata: {
        auth_user_id: account.profile.auth_user_id,
        user_id: account.profile.id,
        plan: BILLING_PLAN,
        source: "web_onboarding",
        trial_days: "3",
      },
      subscription_data: {
        trial_period_days: 3,
        metadata: {
          auth_user_id: account.profile.auth_user_id,
          user_id: account.profile.id,
          plan: BILLING_PLAN,
          source: "web_onboarding",
          trial_days: "3",
        },
      },
      success_url: `${returnBaseUrl}/onboarding/sukces?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${returnBaseUrl}/onboarding/anulowano`,
    });

    checkoutUrl = session.url;
  } catch (error) {
    console.error("createCheckoutRoute failed", error);
    return localRedirect(
      request,
      encoded(
        "/onboarding/platnosc",
        checkoutConfigErrorMessage(error),
      ),
    );
  }

  if (!checkoutUrl) {
    return localRedirect(
      request,
      encoded("/onboarding/platnosc", "Nie udało się utworzyć linku płatności."),
    );
  }

  const trustedCheckoutUrl = trustedExternalUrl(checkoutUrl, [
    "https://checkout.stripe.com",
  ]);
  if (!trustedCheckoutUrl) {
    return localRedirect(
      request,
      encoded(
        "/onboarding/platnosc",
        "Nie udało się bezpiecznie otworzyć płatności.",
      ),
    );
  }

  return NextResponse.redirect(trustedCheckoutUrl, { status: 303 });
}

// GET: interstitial navigates here via nextUrl after showing the loading screen.
export async function GET(request: Request) {
  return handleCheckout(request);
}

// POST: platnosc page form submits here directly.
export async function POST(request: Request) {
  return handleCheckout(request);
}
