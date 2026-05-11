import { NextResponse } from "next/server";
import { activateBetaAccess } from "@/lib/api/onboarding";

export const dynamic = "force-dynamic";

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

function localRedirect(request: Request, path: string) {
  return NextResponse.redirect(new URL(path, request.url), { status: 303 });
}

export async function POST(request: Request) {
  try {
    await activateBetaAccess();
  } catch (error) {
    console.error("activateBetaAccess route failed", error);
    return localRedirect(
      request,
      encoded(
        "/onboarding/platnosc",
        "Nie udało się aktywować dostępu beta dla tego konta.",
      ),
    );
  }

  return localRedirect(request, "/onboarding/google");
}
