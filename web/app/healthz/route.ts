export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    status: "ok",
    phase: "1B",
    readiness: "phase1b-web",
    service: "agent-oze-web",
    timestamp: new Date().toISOString(),
  });
}
