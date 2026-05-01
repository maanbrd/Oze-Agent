export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    status: "ok",
    phase: "1B",
    service: "agent-oze-web",
    readiness: "phase1b-web",
    timestamp: new Date().toISOString(),
  });
}
