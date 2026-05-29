import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { fastApiBaseUrl } from "@/lib/api/base-url";

type ProgressPayload = {
  step: "sheets" | "calendar" | "drive" | "done";
  elapsed_ms: number;
  error?: { code: string; message: string };
};

export async function GET(): Promise<Response> {
  const account = await getCurrentAccount();
  if (!account.authenticated || !account.accessToken) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const base = fastApiBaseUrl();
  if (!base) {
    return NextResponse.json<ProgressPayload>(
      { step: "sheets", elapsed_ms: 0 },
      { status: 200 },
    );
  }

  const upstream = await fetch(`${base}/api/onboarding/resources-progress`, {
    headers: { Authorization: `Bearer ${account.accessToken}` },
    cache: "no-store",
  });

  if (!upstream.ok) {
    return NextResponse.json(
      { error: "upstream_error", status: upstream.status },
      { status: 502 },
    );
  }

  const data = (await upstream.json()) as ProgressPayload;
  return NextResponse.json(data, {
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "application/json",
    },
  });
}
