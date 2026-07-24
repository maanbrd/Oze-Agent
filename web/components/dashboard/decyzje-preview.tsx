"use client";

import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import type { PendingClient } from "@/lib/api/decisions";

const GREEN = "#3DFF7A";
const AMBER = "#FBBF24";
const TELEGRAM_BOT_URL = "https://t.me/AgentOZE_Bot";

export function DecyzjePreview({
  initialClients,
  fetchedAt,
  sourceState,
}: {
  initialClients: PendingClient[];
  fetchedAt: string;
  sourceState: "live" | "unavailable";
}) {
  const clients = [...initialClients].sort((a, b) => b.staleDays - a.staleDays);

  return (
    <main style={{ padding: "32px 24px", color: "#fff" }}>
      <div style={{ maxWidth: 1040, margin: "0 auto" }}>
        {sourceState === "unavailable" ? (
          <div style={warningStyle}>
            <strong style={{ color: AMBER }}>Brak danych z Google Sheets.</strong>{" "}
            Spróbuj ponownie później lub sprawdź połączenie Google.
          </div>
        ) : (
          <div style={freshnessStyle}>
            <span aria-hidden="true" style={liveDotStyle} />
            <span>Live z Google Sheets</span>
            <DataFreshnessBadge fetchedAt={fetchedAt} />
          </div>
        )}

        <section style={introStyle}>
          <div>
            <div style={eyebrowStyle}>Wymagają decyzji</div>
            <h1 style={{ margin: "8px 0", fontSize: "clamp(28px, 4vw, 40px)" }}>
              {clients.length === 0
                ? "Brak zaległych decyzji"
                : `${clients.length} ${clients.length === 1 ? "klient czeka" : "klientów czeka"}`}
            </h1>
            <p style={{ margin: 0, color: "rgba(255,255,255,.62)", lineHeight: 1.6 }}>
              Ten widok jest tylko do odczytu. Zmiany statusu, notatki i terminy
              zatwierdzaj w Telegramie — agent pokaże kartę potwierdzenia przed zapisem.
            </p>
          </div>
          <a href={TELEGRAM_BOT_URL} target="_blank" rel="noopener noreferrer" style={telegramButtonStyle}>
            Otwórz Agenta w Telegramie
          </a>
        </section>

        <div style={{ display: "grid", gap: 12 }}>
          {clients.map((client) => <ReadOnlyClientCard key={client.id} client={client} />)}
        </div>
      </div>
    </main>
  );
}

function ReadOnlyClientCard({ client }: { client: PendingClient }) {
  return (
    <article style={cardStyle}>
      <div>
        <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
          <strong style={{ fontSize: 17 }}>{client.fullName}</strong>
          <span style={{ color: "rgba(255,255,255,.55)", fontSize: 13 }}>
            {client.city}{client.product ? ` · ${client.product}` : ""}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <span style={pillStyle}>{client.status}</span>
          <span style={{ ...pillStyle, color: client.staleDays >= 14 ? "#F87171" : AMBER }}>
            Bez kontaktu: {client.staleDays} dni
          </span>
          {client.nextAction ? <span style={pillStyle}>Następny krok: {client.nextAction}</span> : null}
        </div>
        {client.notes ? (
          <p style={{ margin: "12px 0 0", color: "rgba(255,255,255,.65)", lineHeight: 1.5 }}>
            {client.notes}
          </p>
        ) : null}
      </div>
      <a
        href={TELEGRAM_BOT_URL}
        target="_blank"
        rel="noopener noreferrer"
        style={cardActionStyle}
        aria-label={`Podejmij decyzję o kliencie ${client.fullName} w Telegramie`}
      >
        Podejmij decyzję w Telegramie
      </a>
    </article>
  );
}

const warningStyle = {
  padding: "12px 16px", border: `1px solid ${AMBER}66`, borderRadius: 10,
  background: `${AMBER}12`, marginBottom: 20, lineHeight: 1.5,
} as const;
const freshnessStyle = {
  display: "flex", alignItems: "center", gap: 8, marginBottom: 18,
  color: "rgba(255,255,255,.6)", fontSize: 12,
} as const;
const liveDotStyle = {
  width: 7, height: 7, borderRadius: 999, background: GREEN, boxShadow: `0 0 9px ${GREEN}`,
} as const;
const introStyle = {
  display: "flex", justifyContent: "space-between", alignItems: "center", gap: 24,
  flexWrap: "wrap", padding: 24, marginBottom: 22, border: `1px solid ${GREEN}35`,
  borderLeft: `4px solid ${GREEN}`, borderRadius: 14, background: `${GREEN}08`,
} as const;
const eyebrowStyle = {
  color: GREEN, fontSize: 12, fontWeight: 800, letterSpacing: 1.5, textTransform: "uppercase",
} as const;
const telegramButtonStyle = {
  color: "#050607", background: GREEN, padding: "12px 18px", borderRadius: 999,
  fontWeight: 750, textDecoration: "none", whiteSpace: "nowrap",
} as const;
const cardStyle = {
  display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20,
  flexWrap: "wrap", padding: 18, border: "1px solid rgba(255,255,255,.09)",
  borderRadius: 14, background: "rgba(255,255,255,.03)",
} as const;
const pillStyle = {
  padding: "4px 9px", borderRadius: 999, border: "1px solid rgba(255,255,255,.12)",
  color: "rgba(255,255,255,.76)", fontSize: 12,
} as const;
const cardActionStyle = {
  color: GREEN, border: `1px solid ${GREEN}66`, padding: "9px 14px", borderRadius: 999,
  textDecoration: "none", fontSize: 13, fontWeight: 700,
} as const;
