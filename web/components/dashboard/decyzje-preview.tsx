"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FunnelStatus } from "@/lib/crm/types";

const G = "#3DFF7A";
const RED = "#EF4444";
const AMBER = "#FBBF24";

type Transition = {
  next: FunnelStatus;
  label: string;
  tone: "happy" | "stay" | "out";
};

const TRANSITIONS: Partial<Record<FunnelStatus, Transition[]>> = {
  "Nowy lead": [
    { next: "Spotkanie umówione", label: "✓ Umówione", tone: "happy" },
    { next: "Nowy lead", label: "Czeka na kontakt", tone: "stay" },
    { next: "Odrzucone", label: "✗ Odrzucone", tone: "out" },
  ],
  "Spotkanie umówione": [
    { next: "Spotkanie odbyte", label: "✓ Odbyte", tone: "happy" },
    { next: "Spotkanie umówione", label: "Nadal czeka", tone: "stay" },
    { next: "Nieaktywny", label: "✗ Nieaktywny", tone: "out" },
  ],
  "Spotkanie odbyte": [
    { next: "Oferta wysłana", label: "✓ Wysłałem ofertę", tone: "happy" },
    { next: "Spotkanie odbyte", label: "Jeszcze przygotowuję", tone: "stay" },
    { next: "Nieaktywny", label: "✗ Nieaktywny", tone: "out" },
  ],
  "Oferta wysłana": [
    { next: "Podpisane", label: "✓ Podpisane", tone: "happy" },
    { next: "Oferta wysłana", label: "Czekam na decyzję", tone: "stay" },
    { next: "Rezygnacja z umowy", label: "✗ Rezygnacja", tone: "out" },
  ],
  "Podpisane": [
    { next: "Zamontowana", label: "✓ Zamontowana", tone: "happy" },
    { next: "Podpisane", label: "Czeka na montaż", tone: "stay" },
    { next: "Rezygnacja z umowy", label: "✗ Rezygnacja", tone: "out" },
  ],
};

type MockClient = {
  id: string;
  fullName: string;
  city: string;
  status: FunnelStatus;
  staleDays: number;
  product: string;
  lastNote: string;
};

const MOCK_CLIENTS: MockClient[] = [
  {
    id: "c1",
    fullName: "Magdalena Kowal",
    city: "Gdańsk",
    status: "Nowy lead",
    staleDays: 15,
    product: "PV 6kW",
    lastNote: "Polecenie od p. Kowalskiego, czeka na pierwszy kontakt",
  },
  {
    id: "c2",
    fullName: "Robert Lewandowski",
    city: "Kraków",
    status: "Oferta wysłana",
    staleDays: 12,
    product: "PV 8kW + magazyn 10kWh",
    lastNote: "Oferta poszła 25.04, miał zapytać żonę",
  },
  {
    id: "c3",
    fullName: "Anna Nowicka",
    city: "Płock",
    status: "Spotkanie umówione",
    staleDays: 8,
    product: "Pompa ciepła",
    lastNote: "Spotkanie 28.04, nie odebrał potwierdzającego",
  },
  {
    id: "c4",
    fullName: "Aleksandra Mazur",
    city: "Poznań",
    status: "Oferta wysłana",
    staleDays: 7,
    product: "PV 10kW",
    lastNote: "Druga wersja oferty z mniejszą mocą",
  },
  {
    id: "c5",
    fullName: "Marek Wiśniewski",
    city: "Warszawa",
    status: "Spotkanie odbyte",
    staleDays: 5,
    product: "PV 6kW + magazyn",
    lastNote: "Spotkanie poszło dobrze, zapowiedziałem ofertę na piątek",
  },
  {
    id: "c6",
    fullName: "Tomasz Zieliński",
    city: "Wrocław",
    status: "Spotkanie umówione",
    staleDays: 4,
    product: "PV 5kW",
    lastNote: "Pierwszy lead z fb-ads, umówione na sobotę",
  },
  {
    id: "c7",
    fullName: "Krzysztof Borowski",
    city: "Łódź",
    status: "Podpisane",
    staleDays: 18,
    product: "PV 12kW + magazyn 15kWh",
    lastNote: "Czeka na termin montażu, ekipa zajęta do końca maja",
  },
];

type ToastState = {
  clientId: string;
  clientName: string;
  oldStatus: FunnelStatus;
  newStatus: FunnelStatus;
  expiresAt: number;
};

export function DecyzjePreview() {
  const [clients, setClients] = useState<MockClient[]>(MOCK_CLIENTS);
  const [decided, setDecided] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<ToastState | null>(null);
  const [tick, setTick] = useState(0); // re-render for countdown
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!toast) {
      if (countdownTimer.current) clearInterval(countdownTimer.current);
      return;
    }
    countdownTimer.current = setInterval(() => setTick((t) => t + 1), 250);
    return () => {
      if (countdownTimer.current) clearInterval(countdownTimer.current);
    };
  }, [toast]);

  const visibleClients = useMemo(
    () =>
      clients
        .filter((c) => !decided.has(c.id))
        .sort((a, b) => b.staleDays - a.staleDays),
    [clients, decided],
  );

  const decideClient = (client: MockClient, transition: Transition) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);

    if (transition.tone === "stay") {
      // "Nadal czeka" — no real change, just reset stale counter visually + dismiss
      setClients((prev) =>
        prev.map((c) => (c.id === client.id ? { ...c, staleDays: 0 } : c)),
      );
      setDecided((prev) => new Set(prev).add(client.id));
      setToast({
        clientId: client.id,
        clientName: client.fullName,
        oldStatus: client.status,
        newStatus: client.status,
        expiresAt: Date.now() + 5000,
      });
    } else {
      setClients((prev) =>
        prev.map((c) => (c.id === client.id ? { ...c, status: transition.next } : c)),
      );
      setDecided((prev) => new Set(prev).add(client.id));
      setToast({
        clientId: client.id,
        clientName: client.fullName,
        oldStatus: client.status,
        newStatus: transition.next,
        expiresAt: Date.now() + 5000,
      });
    }

    toastTimer.current = setTimeout(() => setToast(null), 5000);
  };

  const undoToast = () => {
    if (!toast) return;
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setClients((prev) =>
      prev.map((c) => (c.id === toast.clientId ? { ...c, status: toast.oldStatus } : c)),
    );
    setDecided((prev) => {
      const next = new Set(prev);
      next.delete(toast.clientId);
      return next;
    });
    setToast(null);
  };

  const resetAll = () => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setClients(MOCK_CLIENTS);
    setDecided(new Set());
    setToast(null);
  };

  const remainingMs = toast ? Math.max(0, toast.expiresAt - Date.now()) : 0;
  // tick is referenced just to force re-render every 250ms while toast is alive
  void tick;
  const remainingSec = Math.ceil(remainingMs / 1000);

  return (
    <div style={{ padding: "32px 24px", color: "#fff" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        {/* Demo banner */}
        <div
          style={{
            border: `1px solid ${AMBER}66`,
            background: `${AMBER}14`,
            padding: "12px 16px",
            borderRadius: 10,
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 24,
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontSize: 18 }}>🧪</span>
          <div style={{ flex: 1, fontSize: 13.5, lineHeight: 1.5, color: "rgba(255,255,255,0.9)" }}>
            <strong style={{ color: AMBER }}>Prototyp UI.</strong> Klik = zmiana w lokalnym stanie
            tej karty + 5-sekundowy „Cofnij". <em>Nic się nie zapisuje do Sheets.</em> Decyzje:
            kontekstowe 3 przyciski per status, bez modalu, undo na toaście.
          </div>
          <button
            type="button"
            onClick={resetAll}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.2)",
              color: "rgba(255,255,255,0.85)",
              padding: "8px 14px",
              borderRadius: 999,
              fontSize: 12,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            ↻ Reset listy
          </button>
        </div>

        {/* Section header */}
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontSize: 11.5,
              fontWeight: 700,
              letterSpacing: 1.6,
              textTransform: "uppercase",
              color: G,
              marginBottom: 8,
            }}
          >
            — Wymagają decyzji
          </div>
          <h1
            style={{
              fontSize: "clamp(26px, 3.4vw, 36px)",
              fontWeight: 600,
              margin: 0,
              lineHeight: 1.1,
            }}
          >
            {visibleClients.length === 0
              ? "Czysto. Wszystko zdecydowane."
              : `${visibleClients.length} ${visibleClients.length === 1 ? "klient czeka" : visibleClients.length < 5 ? "klientów czeka" : "klientów czeka"} na decyzję`}
          </h1>
          <p style={{ marginTop: 8, color: "rgba(255,255,255,0.55)", fontSize: 14, maxWidth: 640 }}>
            Najpierw najstarsze. Trzy przyciski dobrane do aktualnego statusu — przesuń dalej,
            zostaw, zamknij.
          </p>
        </div>

        {/* Cards */}
        {visibleClients.length === 0 ? (
          <EmptyState onReset={resetAll} />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {visibleClients.map((c) => (
              <ClientRow key={c.id} client={c} onDecide={decideClient} />
            ))}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: "fixed",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(20, 24, 28, 0.96)",
            border: `1px solid ${G}55`,
            borderRadius: 12,
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: 16,
            color: "#fff",
            fontSize: 14,
            boxShadow: "0 16px 40px rgba(0,0,0,0.5)",
            zIndex: 100,
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
          }}
        >
          <div>
            <strong style={{ color: G }}>{toast.clientName}</strong>
            {toast.oldStatus === toast.newStatus ? (
              <> · zostaje w „{toast.oldStatus}"</>
            ) : (
              <>
                {" · "}„{toast.oldStatus}" → <strong>„{toast.newStatus}"</strong>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={undoToast}
            style={{
              background: "transparent",
              border: `1px solid ${G}`,
              color: G,
              padding: "6px 14px",
              borderRadius: 999,
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            ↶ Cofnij ({remainingSec}s)
          </button>
        </div>
      )}
    </div>
  );
}

function ClientRow({
  client,
  onDecide,
}: {
  client: MockClient;
  onDecide: (client: MockClient, transition: Transition) => void;
}) {
  const transitions = TRANSITIONS[client.status] ?? [];
  const stalenessColor = client.staleDays >= 10 ? RED : client.staleDays >= 7 ? AMBER : G;
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 14,
        padding: 18,
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) auto",
        gap: 18,
        alignItems: "center",
      }}
    >
      {/* Left: client info */}
      <div style={{ minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <div style={{ fontSize: 17, fontWeight: 600 }}>{client.fullName}</div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.55)" }}>
            {client.city} · {client.product}
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginTop: 8,
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              fontSize: 11.5,
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: 999,
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "#fff",
            }}
          >
            {client.status}
          </span>
          <span
            style={{
              fontSize: 12,
              color: stalenessColor,
              fontWeight: 600,
            }}
          >
            ● bez ruchu od {client.staleDays} {client.staleDays === 1 ? "dnia" : "dni"}
          </span>
        </div>
        <p
          style={{
            margin: "10px 0 0",
            fontSize: 13.5,
            color: "rgba(255,255,255,0.6)",
            lineHeight: 1.5,
          }}
        >
          {client.lastNote}
        </p>
      </div>

      {/* Right: action buttons */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 220 }}>
        {transitions.map((t) => (
          <ActionButton
            key={t.label}
            tone={t.tone}
            onClick={() => onDecide(client, t)}
            label={t.label}
          />
        ))}
      </div>
    </div>
  );
}

function ActionButton({
  tone,
  label,
  onClick,
}: {
  tone: "happy" | "stay" | "out";
  label: string;
  onClick: () => void;
}) {
  const palette =
    tone === "happy"
      ? { bg: G, color: "#000", border: G, hoverBg: "#5cff90" }
      : tone === "out"
        ? {
            bg: "transparent",
            color: RED,
            border: `${RED}66`,
            hoverBg: `${RED}1A`,
          }
        : {
            bg: "transparent",
            color: "rgba(255,255,255,0.7)",
            border: "rgba(255,255,255,0.18)",
            hoverBg: "rgba(255,255,255,0.06)",
          };

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = palette.hoverBg;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = palette.bg;
      }}
      style={{
        background: palette.bg,
        color: palette.color,
        border: `1px solid ${palette.border}`,
        padding: "10px 14px",
        borderRadius: 10,
        fontSize: 13,
        fontWeight: tone === "happy" ? 700 : 500,
        cursor: "pointer",
        textAlign: "left",
        fontFamily: "inherit",
        transition: "background 0.15s",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </button>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div
      style={{
        border: "1px dashed rgba(255,255,255,0.15)",
        borderRadius: 14,
        padding: 48,
        textAlign: "center",
        color: "rgba(255,255,255,0.6)",
      }}
    >
      <div style={{ fontSize: 36, marginBottom: 12 }}>✓</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 6 }}>
        Lejek aktualny.
      </div>
      <div style={{ fontSize: 13.5, marginBottom: 20 }}>
        Zdecydowałeś o wszystkich klientach z zaległościami.
      </div>
      <button
        type="button"
        onClick={onReset}
        style={{
          background: "transparent",
          border: `1px solid ${G}`,
          color: G,
          padding: "10px 20px",
          borderRadius: 999,
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          fontFamily: "inherit",
        }}
      >
        ↻ Reset prototypu
      </button>
    </div>
  );
}
