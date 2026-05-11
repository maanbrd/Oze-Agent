import { NextResponse } from "next/server";
import { getTelegramStatusOrThrow } from "@/lib/api/onboarding";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const status = await getTelegramStatusOrThrow();
    return NextResponse.json(
      {
        ok: true,
        ...status,
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    );
  } catch (error) {
    console.error("telegram-status route failed", error);
    return NextResponse.json(
      {
        ok: false,
        error: "status_check_failed",
        paired: false,
        telegramId: null,
        code: null,
        expiresAt: null,
      },
      {
        status: 502,
        headers: {
          "Cache-Control": "no-store",
        },
      },
    );
  }
}
