"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { toast as sonnerToast } from "sonner";
import { showSuccess, showError } from "@/lib/ui/toast";
import {
  formatScheduleLabel,
  pad2,
  stalenessColor,
  tomorrowDateString,
  transitionsForStatus,
  type Transition,
  type TransitionTone,
} from "@/lib/crm/decisions";
import type { PendingClient } from "@/lib/api/decisions";
import {
  changeClientStatusAction,
  scheduleClientCallAction,
  touchClientContactAction,
} from "@/app/(app)/dashboard/decyzje-preview/actions";

const G = "#3DFF7A";
const RED = "#EF4444";
const AMBER = "#FBBF24";

type ScheduleDraft = {
  client: PendingClient;
  date: string;
  time: string;
  note: string;
  mode: "create" | "overwrite";
};

type ReScheduleAsk = {
  client: PendingClient;
};

function defaultPrefilledNote(client: PendingClient): string {
  const product = client.product?.trim();
  return product
    ? `Telefon: zapytaj o decyzję ws. ${product}`
    : "Telefon: zapytaj o decyzję ws. oferty";
}

export function DecyzjePreview({
  initialClients,
  fetchedAt,
  sourceState,
}: {
  initialClients: PendingClient[];
  fetchedAt: string;
  sourceState: "live" | "unavailable";
}) {
  const [clients, setClients] = useState<PendingClient[]>(initialClients);
  const [decided, setDecided] = useState<Set<string>>(new Set());
  const [scheduleDraft, setScheduleDraft] = useState<ScheduleDraft | null>(null);
  const [reScheduleAsk, setReScheduleAsk] = useState<ReScheduleAsk | null>(null);
  const [, startTransition] = useTransition();

  // Server component passes `key={fetchedAt}` so the component re-mounts on
  // every server-side data refresh — that is what gives us a clean
  // `initialClients` snapshot without a setState-in-effect resync hack.

  const visibleClients = useMemo(
    () =>
      clients
        .filter((c) => !decided.has(c.id))
        .sort((a, b) => b.staleDays - a.staleDays),
    [clients, decided],
  );

  const decideClient = (client: PendingClient, transition: Transition) => {
    // Optimistic state update.
    setDecided((prev) => new Set(prev).add(client.id));
    if (transition.tone !== "stay") {
      setClients((prev) =>
        prev.map((c) => (c.id === client.id ? { ...c, status: transition.next } : c)),
      );
    }

    const undoLabel =
      client.status === transition.next
        ? `${client.fullName} · zostaje w „${client.status}"`
        : `${client.fullName} · „${client.status}" → „${transition.next}"`;

    // Status-change toasts use 10 000 ms to preserve the original undo window.
    // showAction uses a fixed 6 s; we call sonnerToast() directly for this case.
    sonnerToast("Zmieniono status", {
      description: undoLabel,
      duration: 10_000,
      action: {
        label: "Cofnij",
        onClick: () => {
          // Optimistic local revert.
          setDecided((prev) => {
            const next = new Set(prev);
            next.delete(client.id);
            return next;
          });
          setClients((prev) =>
            prev.map((c) => (c.id === client.id ? { ...c, status: client.status } : c)),
          );

          startTransition(async () => {
            // "Stay" undo is a no-op semantically — column J was already bumped
            // and there is no reverse for that in MVP.
            if (client.status === transition.next) return;
            const result = await changeClientStatusAction(client.row, client.status);
            if (!result.ok) {
              showError(
                "Cofnięcie nie powiodło się",
                `Sprawdź ${client.fullName} w Sheets.`,
              );
            }
          });
        },
      },
    });

    startTransition(async () => {
      const result =
        transition.tone === "stay"
          ? await touchClientContactAction(client.row)
          : await changeClientStatusAction(client.row, transition.next);

      if (!result.ok) {
        // Revert optimistic state.
        setDecided((prev) => {
          const next = new Set(prev);
          next.delete(client.id);
          return next;
        });
        if (transition.tone !== "stay") {
          setClients((prev) =>
            prev.map((c) => (c.id === client.id ? { ...c, status: client.status } : c)),
          );
        }
        showError(
          "Nie udało się zapisać w Sheets",
          `${client.fullName}. Spróbuj ponownie.`,
        );
      }
    });
  };

  const requestSchedule = (client: PendingClient) => {
    if (client.calendarEventId && client.calendarEventId.trim().length > 0) {
      setReScheduleAsk({ client });
      return;
    }
    setScheduleDraft({
      client,
      date: tomorrowDateString(),
      time: "10:00",
      note: defaultPrefilledNote(client),
      mode: "create",
    });
  };

  const closeReSchedule = () => setReScheduleAsk(null);

  const proceedReScheduleAsOverwrite = (client: PendingClient) => {
    setReScheduleAsk(null);
    let date = tomorrowDateString();
    let time = "10:00";
    const existing = client.nextActionAt;
    if (existing && existing.length >= 10) {
      date = existing.slice(0, 10);
      const tMatch = existing.match(/T(\d{2}):(\d{2})/);
      if (tMatch) time = `${tMatch[1]}:${tMatch[2]}`;
    }
    setScheduleDraft({
      client,
      date,
      time,
      note: defaultPrefilledNote(client),
      mode: "overwrite",
    });
  };

  const proceedReScheduleAsCancelOnly = (client: PendingClient) => {
    setReScheduleAsk(null);

    setDecided((prev) => new Set(prev).add(client.id));
    showSuccess("Telefon anulowany", `Klient: ${client.fullName}`);

    startTransition(async () => {
      const result = await scheduleClientCallAction({
        row: client.row,
        date: tomorrowDateString(),
        time: "10:00",
        note: "",
        mode: "cancel-only",
      });
      if (!result.ok) {
        setDecided((prev) => {
          const next = new Set(prev);
          next.delete(client.id);
          return next;
        });
        showError(
          "Nie udało się anulować telefonu",
          `${client.fullName} — sprawdź Calendar ręcznie.`,
        );
      }
    });
  };

  const closeSchedule = () => setScheduleDraft(null);

  const submitSchedule = (draft: ScheduleDraft) => {
    setDecided((prev) => new Set(prev).add(draft.client.id));
    showSuccess(
      "Zaplanowano telefon",
      `Klient: ${draft.client.fullName} · ${formatScheduleLabel(draft.date, draft.time)}`,
    );
    setScheduleDraft(null);

    startTransition(async () => {
      const result = await scheduleClientCallAction({
        row: draft.client.row,
        date: draft.date,
        time: draft.time,
        note: draft.note,
        mode: draft.mode,
      });
      if (!result.ok) {
        setDecided((prev) => {
          const next = new Set(prev);
          next.delete(draft.client.id);
          return next;
        });
        showError(
          "Nie udało się zapisać telefonu w Calendar",
          `${draft.client.fullName} — spróbuj ponownie.`,
        );
      }
    });
  };

  return (
    <div style={{ padding: "32px 24px", color: "#fff" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        {/* Source banner */}
        {sourceState === "unavailable" ? (
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
            <span style={{ fontSize: 18 }}>⚠️</span>
            <div style={{ flex: 1, fontSize: 13.5, lineHeight: 1.5, color: "rgba(255,255,255,0.9)" }}>
              <strong style={{ color: AMBER }}>Brak danych z Sheets.</strong> Możliwe że konto
              jeszcze nie ma sparowanego Google albo backend jest chwilowo niedostępny.
            </div>
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 18,
              fontSize: 12,
              color: "rgba(255,255,255,0.55)",
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: 3,
                background: G,
                boxShadow: `0 0 8px ${G}`,
              }}
            />
            <span style={{ color: "#fff", fontWeight: 600 }}>Live z Google Sheets</span>
            <DataFreshnessBadge fetchedAt={fetchedAt} />
          </div>
        )}

        {/* Explainer — po co ta sekcja */}
        <div
          style={{
            border: `1px solid ${G}40`,
            borderLeft: `4px solid ${G}`,
            background: `linear-gradient(90deg, ${G}10 0%, rgba(255,255,255,0.025) 35%)`,
            borderRadius: 14,
            padding: "22px 26px",
            marginBottom: 24,
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: 14,
            boxShadow: `0 0 24px ${G}14`,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: 1.6,
                textTransform: "uppercase",
                color: G,
                background: `${G}1A`,
                padding: "6px 14px",
                borderRadius: 999,
                border: `1px solid ${G}55`,
              }}
            >
              <span aria-hidden="true" style={{ fontSize: 14 }}>💡</span>
              Po co ta sekcja
            </span>
          </div>
          <p
            style={{
              margin: 0,
              fontSize: 16,
              lineHeight: 1.6,
              color: "#fff",
              fontWeight: 500,
            }}
          >
            To Twoja codzienna 2-minutowa decyzja: który klient idzie dalej, kto jeszcze
            czeka, kogo wyrzucasz z&nbsp;lejka. Bez tego dashboard pokazuje śmieci, a&nbsp;Ty{" "}
            <strong style={{ color: G }}>tracisz pieniądze</strong>.
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
              body="Jeden klik = klient idzie na następny etap. Sheets zapisze się sam."
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
              : `${visibleClients.length} ${visibleClients.length === 1 ? "klient czeka" : "klientów czeka"} na decyzję`}
          </h1>
          <p style={{ marginTop: 8, color: "rgba(255,255,255,0.55)", fontSize: 14, maxWidth: 640 }}>
            Najpierw najstarsze. Trzy przyciski dobrane do aktualnego statusu — przesuń dalej,
            zostaw, zamknij.
          </p>
        </div>

        {/* Cards */}
        {visibleClients.length === 0 ? (
          <EmptyState />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {visibleClients.map((c) => (
              <ClientRow
                key={c.id}
                client={c}
                onDecide={decideClient}
                onSchedule={requestSchedule}
              />
            ))}
          </div>
        )}
      </div>

      {/* Re-schedule confirmation */}
      {reScheduleAsk && (
        <ReScheduleConfirmModal
          client={reScheduleAsk.client}
          onClose={closeReSchedule}
          onOverwrite={proceedReScheduleAsOverwrite}
          onCancelOnly={proceedReScheduleAsCancelOnly}
        />
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
  client: PendingClient;
  onDecide: (client: PendingClient, transition: Transition) => void;
  onSchedule: (client: PendingClient) => void;
}) {
  const transitions = transitionsForStatus(client.status);
  const stalenessHex = stalenessColor(client.staleDays);
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
      <div style={{ minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <div style={{ fontSize: 17, fontWeight: 600 }}>{client.fullName}</div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.55)" }}>
            {client.city}
            {client.product ? ` · ${client.product}` : ""}
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
              color: stalenessHex,
              fontWeight: 600,
            }}
          >
            ● bez ruchu od {client.staleDays} {client.staleDays === 1 ? "dnia" : "dni"}
          </span>
          {client.calendarEventId ? (
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 500,
                padding: "3px 8px",
                borderRadius: 999,
                background: `${G}14`,
                border: `1px solid ${G}55`,
                color: G,
              }}
              title="Klient ma już zaplanowany telefon w Calendar."
            >
              📅 Telefon zaplanowany
            </span>
          ) : null}
        </div>
        {client.notes ? (
          <p
            style={{
              margin: "10px 0 6px",
              fontSize: 13.5,
              color: "rgba(255,255,255,0.6)",
              lineHeight: 1.5,
            }}
          >
            {client.notes}
          </p>
        ) : null}
        <button
          type="button"
          onClick={() => onSchedule(client)}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = `${G}26`;
            e.currentTarget.style.borderColor = G;
            e.currentTarget.style.boxShadow = `0 0 18px ${G}40`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = `${G}14`;
            e.currentTarget.style.borderColor = `${G}66`;
            e.currentTarget.style.boxShadow = "none";
          }}
          style={{
            marginTop: 12,
            background: `${G}14`,
            border: `1px solid ${G}66`,
            padding: "9px 16px",
            color: G,
            fontSize: 13.5,
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "inherit",
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            borderRadius: 999,
            transition: "background 0.15s, border-color 0.15s, box-shadow 0.15s",
          }}
        >
          <span aria-hidden="true" style={{ fontSize: 15 }}>📞</span>
          Zaplanuj kontakt telefoniczny
        </button>
      </div>

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
  tone: TransitionTone;
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

function ReScheduleConfirmModal({
  client,
  onClose,
  onOverwrite,
  onCancelOnly,
}: {
  client: PendingClient;
  onClose: () => void;
  onOverwrite: (c: PendingClient) => void;
  onCancelOnly: (c: PendingClient) => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const existing = client.nextActionAt;
  let existingLabel = "(brak daty w Sheets)";
  if (existing) {
    const dayNum = parseInt(existing.slice(8, 10), 10);
    const monthNum = parseInt(existing.slice(5, 7), 10);
    if (existing.length >= 16 && Number.isFinite(dayNum) && Number.isFinite(monthNum)) {
      existingLabel = `${pad2(dayNum)}.${pad2(monthNum)} ${existing.slice(11, 16)}`;
    } else {
      existingLabel = existing;
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="reschedule-modal-title"
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
          maxWidth: 460,
          background: "#0b0e12",
          border: `1px solid ${AMBER}55`,
          borderRadius: 16,
          padding: 22,
          color: "#fff",
          boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1.4,
            textTransform: "uppercase",
            color: AMBER,
            marginBottom: 10,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span aria-hidden="true">⚠️</span>
          Klient ma już zaplanowany telefon
        </div>
        <h2
          id="reschedule-modal-title"
          style={{ margin: 0, fontSize: 19, fontWeight: 600, lineHeight: 1.3 }}
        >
          {client.fullName}
        </h2>
        <p style={{ margin: "12px 0 18px", fontSize: 14, lineHeight: 1.55, color: "rgba(255,255,255,0.78)" }}>
          W Calendar istnieje już zaplanowany telefon na <strong style={{ color: "#fff" }}>{existingLabel}</strong>.
          Co chcesz z nim zrobić?
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <button
            type="button"
            onClick={() => onOverwrite(client)}
            style={{
              background: G,
              border: 0,
              color: "#000",
              padding: "11px 16px",
              borderRadius: 10,
              fontSize: 13.5,
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "inherit",
              textAlign: "left",
              boxShadow: `0 0 16px ${G}40`,
            }}
          >
            ✓ Nadpisz nowym terminem
          </button>
          <button
            type="button"
            onClick={() => onCancelOnly(client)}
            style={{
              background: "transparent",
              border: `1px solid ${RED}66`,
              color: RED,
              padding: "11px 16px",
              borderRadius: 10,
              fontSize: 13.5,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "inherit",
              textAlign: "left",
            }}
          >
            ✗ Usuń stary, nie planuj nowego
          </button>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.18)",
              color: "rgba(255,255,255,0.85)",
              padding: "11px 16px",
              borderRadius: 10,
              fontSize: 13.5,
              cursor: "pointer",
              fontFamily: "inherit",
              textAlign: "left",
            }}
          >
            Anuluj
          </button>
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
              📞 {draft.mode === "overwrite" ? "Nadpisz telefon" : "Zaplanuj kontakt"}
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
            <strong style={{ color: "#fff" }}>{draft.client.city}</strong>
            {draft.client.product ? ` · ${draft.client.product}` : ""}
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
          {draft.client.notes ? (
            <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 12.5 }}>
              {draft.client.notes}
            </div>
          ) : null}
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

function EmptyState() {
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
      <div style={{ fontSize: 13.5 }}>
        Zdecydowałeś o wszystkich klientach z zaległościami. Wróć tu jutro.
      </div>
    </div>
  );
}
