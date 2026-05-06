import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { trustedExternalUrl } from "@/lib/routes";
import {
  checkoutConfigErrorMessage,
  getStripe,
  requireStripeEnv,
  resolveStripePriceId,
} from "@/lib/stripe/server";

type BillingPlan = "monthly" | "yearly";

export const dynamic = "force-dynamic";

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

function planFromForm(formData: FormData): BillingPlan {
  const plan = String(formData.get("plan") ?? "");
  return plan === "yearly" ? "yearly" : "monthly";
}

function localRedirect(request: Request, path: string) {
  return NextResponse.redirect(new URL(path, request.url), { status: 303 });
}

export async function POST(request: Request) {
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

  const formData = await request.formData();
  const plan = planFromForm(formData);
  let checkoutUrl: string | null = null;

  try {
    const { activationPrice, monthlyPrice, yearlyPrice, appUrl } =
      requireStripeEnv();
    const returnBaseUrl = resolveCheckoutReturnBaseUrl(request, appUrl);
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
      encoded("/onboarding/platnosc", "Stripe nie zwrócił linku."),
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
        "Stripe zwrócił nieoczekiwany adres checkoutu.",
      ),
    );
  }

  return NextResponse.redirect(trustedCheckoutUrl, { status: 303 });
}
