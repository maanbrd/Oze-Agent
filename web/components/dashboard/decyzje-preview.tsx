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

type ToastState =
  | {
      kind: "status";
      clientId: string;
      clientName: string;
      oldStatus: FunnelStatus;
      newStatus: FunnelStatus;
      expiresAt: number;
    }
  | {
      kind: "schedule";
      clientId: string;
      clientName: string;
      whenLabel: string;
      expiresAt: number;
    };

type ScheduleDraft = {
  client: MockClient;
  date: string;
  time: string;
  note: string;
};

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function tomorrowDateString(): string {
  const dt = new Date();
  dt.setDate(dt.getDate() + 1);
  return `${dt.getFullYear()}-${pad2(dt.getMonth() + 1)}-${pad2(dt.getDate())}`;
}

const POLISH_DAY_SHORT = ["niedz.", "pn.", "wt.", "śr.", "czw.", "pt.", "sob."];

function formatScheduleLabel(date: string, time: string): string {
  if (!date || !time) return "";
  const [y, m, d] = date.split("-").map((s) => parseInt(s, 10));
  if (!y || !m || !d) return `${date} ${time}`;
  const dt = new Date(y, m - 1, d);
  const dayName = POLISH_DAY_SHORT[dt.getDay()] ?? "";
  return `${pad2(d)}.${pad2(m)} (${dayName}) ${time}`;
}

export function DecyzjePreview() {
  const [clients, setClients] = useState<MockClient[]>(MOCK_CLIENTS);
  const [decided, setDecided] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<ToastState | null>(null);
  const [scheduleDraft, setScheduleDraft] = useState<ScheduleDraft | null>(null);
  const [now, setNow] = useState<number>(() => Date.now());
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!toast) {
      if (countdownTimer.current) clearInterval(countdownTimer.current);
      return;
    }
    countdownTimer.current = setInterval(() => setNow(Date.now()), 250);
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
      setClients((prev) =>
        prev.map((c) => (c.id === client.id ? { ...c, staleDays: 0 } : c)),
      );
      setDecided((prev) => new Set(prev).add(client.id));
      setToast({
        kind: "status",
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
        kind: "status",
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
    if (!toast || toast.kind !== "status") return;
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

  const openSchedule = (client: MockClient) => {
    setScheduleDraft({
      client,
      date: tomorrowDateString(),
      time: "10:00",
      note: `Telefon: zapytaj o decyzję ws. ${client.product}`,
    });
  };

  const closeSchedule = () => setScheduleDraft(null);

  const submitSchedule = (draft: ScheduleDraft) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setDecided((prev) => new Set(prev).add(draft.client.id));
    setToast({
      kind: "schedule",
      clientId: draft.client.id,
      clientName: draft.client.fullName,
      whenLabel: formatScheduleLabel(draft.date, draft.time),
      expiresAt: Date.now() + 5000,
    });
    setScheduleDraft(null);
    toastTimer.current = setTimeout(() => setToast(null), 5000);
  };

  const resetAll = () => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setClients(MOCK_CLIENTS);
    setDecided(new Set());
    setToast(null);
    setScheduleDraft(null);
  };

  const remainingMs = toast ? Math.max(0, toast.expiresAt - now) : 0;
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
            tej karty + 5-sekundowy „Cofnij”. <em>Nic się nie zapisuje do Sheets.</em> Decyzje:
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

        {/* Explainer — po co ta sekcja */}
        <div
          style={{
            border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(255,255,255,0.025)",
            borderRadius: 14,
            padding: "20px 22px",
            marginBottom: 24,
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1.4,
                textTransform: "uppercase",
                color: G,
              }}
            >
              Po co ta sekcja
            </span>
          </div>
          <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.6, color: "rgba(255,255,255,0.85)" }}>
            Lejek kłamie, kiedy zostawiasz w nim klientów, którym właściwie powiedziałeś
            „nie” albo o których po prostu zapomniałeś. „Wymagają decyzji” zbiera tych,
            co stoją za długo w jednym statusie — żeby co dzień zająć Ci 2 minuty na
            posprzątanie i pchnięcie spraw dalej.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: 16,
              marginTop: 4,
            }}
          >
            <ExplainerPoint
              icon="🎯"
              title="Awansuj dalej w lejku"
              body="Jeden klik = klient idzie na następny etap. Bez wchodzenia do Sheets."
            />
            <ExplainerPoint
              icon="🧹"
              title="Wyczyść martwe leady"
              body={"Oznacz „Nieaktywny” / „Rezygnacja” / „Odrzucone” — żeby KPI były prawdziwe."}
            />
            <ExplainerPoint
              icon="📞"
              title="Zaplanuj telefon"
              body="Ustaw datę, godzinę i notatkę — zapisuje się jako 15-min spotkanie w Calendar."
            />
          </div>
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
              <ClientRow
                key={c.id}
                client={c}
                onDecide={decideClient}
                onSchedule={openSchedule}
              />
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
            maxWidth: "calc(100vw - 32px)",
          }}
        >
          {toast.kind === "status" ? (
            <>
              <div>
                <strong style={{ color: G }}>{toast.clientName}</strong>
                {toast.oldStatus === toast.newStatus ? (
                  <> · zostaje w „{toast.oldStatus}”</>
                ) : (
                  <>
                    {" · "}„{toast.oldStatus}” → <strong>„{toast.newStatus}”</strong>
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
            </>
          ) : (
            <div>
              <span style={{ marginRight: 8 }}>📅</span>
              <strong style={{ color: G }}>{toast.clientName}</strong>
              {" · "}
              {toast.whenLabel}
              {" · "}
              <span style={{ color: "rgba(255,255,255,0.6)" }}>15 min · zapisane w Calendar</span>
            </div>
          )}
        </div>
      )}

      {/* Schedule modal */}
      {scheduleDraft && (
        <ScheduleModal
          draft={scheduleDraft}
          onChange={setScheduleDraft}
          onClose={closeSchedule}
          onSubmit={submitSchedule}
        />
      )}
    </div>
  );
}

function ClientRow({
  client,
  onDecide,
  onSchedule,
}: {
  client: MockClient;
  onDecide: (client: MockClient, transition: Transition) => void;
  onSchedule: (client: MockClient) => void;
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
            margin: "10px 0 6px",
            fontSize: 13.5,
            color: "rgba(255,255,255,0.6)",
            lineHeight: 1.5,
          }}
        >
          {client.lastNote}
        </p>
        <button
          type="button"
          onClick={() => onSchedule(client)}
          onMouseEnter={(e) => (e.currentTarget.style.color = G)}
          onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
          style={{
            background: "transparent",
            border: 0,
            padding: "4px 0",
            color: "rgba(255,255,255,0.55)",
            fontSize: 12.5,
            fontWeight: 500,
            cursor: "pointer",
            fontFamily: "inherit",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            transition: "color 0.15s",
          }}
        >
          <span aria-hidden="true">📞</span>
          Zaplanuj kontakt telefoniczny
        </button>
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

function ExplainerPoint({
  icon,
  title,
  body,
}: {
  icon: string;
  title: string;
  body: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
        padding: "12px 14px",
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 10,
      }}
    >
      <span style={{ fontSize: 20, flexShrink: 0, lineHeight: 1.2 }} aria-hidden="true">
        {icon}
      </span>
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 600, color: "#fff", marginBottom: 2 }}>
          {title}
        </div>
        <div style={{ fontSize: 12.5, color: "rgba(255,255,255,0.6)", lineHeight: 1.45 }}>
          {body}
        </div>
      </div>
    </div>
  );
}

function ScheduleModal({
  draft,
  onChange,
  onClose,
  onSubmit,
}: {
  draft: ScheduleDraft;
  onChange: (next: ScheduleDraft) => void;
  onClose: () => void;
  onSubmit: (draft: ScheduleDraft) => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const valid = draft.date.length > 0 && draft.time.length > 0;
  const preview = formatScheduleLabel(draft.date, draft.time);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="schedule-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        zIndex: 200,
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 520,
          background: "#0b0e12",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 16,
          padding: 24,
          color: "#fff",
          boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 14,
            gap: 12,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1.4,
                textTransform: "uppercase",
                color: G,
                marginBottom: 6,
              }}
            >
              📞 Zaplanuj kontakt
            </div>
            <h2
              id="schedule-modal-title"
              style={{ margin: 0, fontSize: 20, fontWeight: 600, lineHeight: 1.25 }}
            >
              {draft.client.fullName}
            </h2>
          </div>
          <button
            type="button"
            aria-label="Zamknij"
            onClick={onClose}
            style={{
              background: "transparent",
              border: 0,
              color: "rgba(255,255,255,0.5)",
              fontSize: 22,
              cursor: "pointer",
              fontFamily: "inherit",
              padding: 0,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 10,
            padding: "12px 14px",
            fontSize: 13,
            color: "rgba(255,255,255,0.7)",
            marginBottom: 18,
            lineHeight: 1.55,
          }}
        >
          <div style={{ marginBottom: 4 }}>
            <strong style={{ color: "#fff" }}>{draft.client.city}</strong> · {draft.client.product}
          </div>
          <div style={{ marginBottom: 4 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
              }}
            >
              {draft.client.status}
            </span>{" "}
            · bez ruchu od {draft.client.staleDays}{" "}
            {draft.client.staleDays === 1 ? "dnia" : "dni"}
          </div>
          <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 12.5 }}>
            {draft.client.lastNote}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
          <label style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", fontWeight: 500 }}>
            Data
            <input
              type="date"
              value={draft.date}
              onChange={(e) => onChange({ ...draft, date: e.target.value })}
              style={{
                marginTop: 6,
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#fff",
                padding: "10px 12px",
                fontSize: 14,
                fontFamily: "inherit",
                colorScheme: "dark",
              }}
            />
          </label>
          <label style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", fontWeight: 500 }}>
            Godzina
            <input
              type="time"
              value={draft.time}
              onChange={(e) => onChange({ ...draft, time: e.target.value })}
              style={{
                marginTop: 6,
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#fff",
                padding: "10px 12px",
                fontSize: 14,
                fontFamily: "inherit",
                colorScheme: "dark",
              }}
            />
          </label>
        </div>

        <label
          style={{
            fontSize: 12,
            color: "rgba(255,255,255,0.7)",
            fontWeight: 500,
            display: "block",
            marginBottom: 14,
          }}
        >
          Notatka (trafi do opisu wydarzenia)
          <textarea
            value={draft.note}
            onChange={(e) => onChange({ ...draft, note: e.target.value })}
            rows={3}
            placeholder="Np. „Zapytaj o decyzję ws. magazynu, omów termin montażu"
            style={{
              marginTop: 6,
              width: "100%",
              background: "rgba(0,0,0,0.4)",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 8,
              color: "#fff",
              padding: "10px 12px",
              fontSize: 13.5,
              fontFamily: "inherit",
              resize: "vertical",
              lineHeight: 1.5,
            }}
          />
        </label>

        <div
          style={{
            background: `${G}10`,
            border: `1px solid ${G}33`,
            borderRadius: 8,
            padding: "10px 12px",
            fontSize: 12.5,
            color: "rgba(255,255,255,0.85)",
            marginBottom: 18,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span aria-hidden="true">📅</span>
          <span>
            <strong style={{ color: G }}>15-min spotkanie w Calendar</strong> ·{" "}
            {preview || "ustaw datę i godzinę"} · pełne dane klienta + notatka w opisie
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.18)",
              color: "rgba(255,255,255,0.85)",
              padding: "10px 18px",
              borderRadius: 999,
              fontSize: 13.5,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            Anuluj
          </button>
          <button
            type="button"
            disabled={!valid}
            onClick={() => onSubmit(draft)}
            style={{
              background: valid ? G : "rgba(61,255,122,0.3)",
              border: 0,
              color: "#000",
              padding: "10px 20px",
              borderRadius: 999,
              fontSize: 13.5,
              fontWeight: 700,
              cursor: valid ? "pointer" : "not-allowed",
              fontFamily: "inherit",
              boxShadow: valid ? `0 0 24px ${G}55` : "none",
            }}
          >
            Zapisz w kalendarzu
          </button>
        </div>
      </div>
    </div>
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
