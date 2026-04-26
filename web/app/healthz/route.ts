export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    status: "ok",
    phase: "0A",
    service: "agent-oze-web",
    timestamp: new Date().toISOString(),
  });
}
