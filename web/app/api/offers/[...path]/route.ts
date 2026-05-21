import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { fastApiBaseUrl } from "@/lib/api/base-url";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path?: string[] }>;
};

const FORWARD_TIMEOUT_MS = 30000;

async function resolvePath(context: RouteContext) {
  const params = await context.params;
  return (params.path ?? []).map(encodeURIComponent).join("/");
}

function copyForwardHeaders(request: Request, accessToken: string) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  headers.set("authorization", `Bearer ${accessToken}`);
  return headers;
}

async function forward(request: Request, context: RouteContext) {
  const account = await getCurrentAccount();
  if (!account.authenticated || !account.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const baseUrl = fastApiBaseUrl();
  if (!baseUrl) {
    return NextResponse.json({ error: "FastAPI not configured" }, { status: 500 });
  }

  const path = await resolvePath(context);
  const sourceUrl = new URL(request.url);
  const targetUrl = new URL(`${baseUrl}/offers/${path}`);
  targetUrl.search = sourceUrl.search;
  targetUrl.searchParams.delete("user_id");

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FORWARD_TIMEOUT_MS);
  try {
    const hasBody = !["GET", "HEAD"].includes(request.method);
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: copyForwardHeaders(request, account.accessToken),
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
      signal: controller.signal,
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
        "content-disposition": response.headers.get("content-disposition") ?? "",
      },
    });
  } catch {
    return NextResponse.json({ error: "Offer API unavailable" }, { status: 502 });
  } finally {
    clearTimeout(timeout);
  }
}

export async function GET(request: Request, context: RouteContext) {
  return forward(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return forward(request, context);
}

export async function PATCH(request: Request, context: RouteContext) {
  return forward(request, context);
}

export async function DELETE(request: Request, context: RouteContext) {
  return forward(request, context);
}
