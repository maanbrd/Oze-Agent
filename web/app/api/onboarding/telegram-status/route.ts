import { NextResponse } from "next/server";
import { getTelegramStatus } from "@/lib/api/onboarding";

export const dynamic = "force-dynamic";

export async function GET() {
  const status = await getTelegramStatus();
  return NextResponse.json(
    status ?? {
      paired: false,
      telegramId: null,
      code: null,
      expiresAt: null,
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
