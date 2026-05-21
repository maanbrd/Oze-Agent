import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { getStripe } from "@/lib/stripe/server";

export const dynamic = "force-dynamic";

function redirectTo(request: Request, path: string) {
  return NextResponse.redirect(new URL(path, request.url), { status: 303 });
}

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

export async function POST(request: Request) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    return redirectTo(request, "/login?next=/platnosci");
  }

  const profile = account.profile;
  if (!profile) {
    return redirectTo(
      request,
      encoded("/platnosci", "Nie znaleziono profilu konta."),
    );
  }

  if (profile.subscription_status !== "trialing") {
    return redirectTo(
      request,
      encoded("/platnosci", "Anulowanie okresu próbnego nie jest dostępne dla tego konta."),
    );
  }

  if (profile.subscription_cancel_at_period_end) {
    return redirectTo(
      request,
      encoded("/platnosci", "Okres próbny jest już anulowany na koniec bieżącego okresu."),
    );
  }

  if (!profile.stripe_subscription_id) {
    return redirectTo(
      request,
      encoded("/platnosci", "Brakuje identyfikatora subskrypcji. Skontaktuj się z obsługą Agent OZE."),
    );
  }

  try {
    await getStripe().subscriptions.update(profile.stripe_subscription_id, {
      cancel_at_period_end: true,
    });
  } catch (error) {
    console.error("cancel trial subscription failed", error);
    return redirectTo(
      request,
      encoded("/platnosci", "Nie udało się anulować okresu próbnego. Spróbuj ponownie za chwilę."),
    );
  }

  return redirectTo(
    request,
    encoded(
      "/platnosci",
      "Dostęp działa do końca okresu próbnego. Opłata nie zostanie naliczona.",
    ),
  );
}
