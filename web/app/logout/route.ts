import { NextResponse } from "next/server";
import {
  createClient,
  missingSupabaseEnvRedirectMessage,
} from "@/lib/supabase/server";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const configError = missingSupabaseEnvRedirectMessage();

  if (configError) {
    url.pathname = "/login";
    url.search = new URLSearchParams({ message: configError }).toString();
    return NextResponse.redirect(url);
  }

  const supabase = await createClient();
  await supabase.auth.signOut();

  url.pathname = "/login";
  url.search = new URLSearchParams({
    message: "Wylogowano. Możesz zalogować się na inne konto.",
  }).toString();

  return NextResponse.redirect(url);
}
