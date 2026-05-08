"use client";

import { type CSSProperties, type FormEvent, useState } from "react";

const contactEmail = "kontakt@oze-agent.pl";
const socialUrl = "https://t.me/OZEAgentBot";

export function FirmaContactForm() {
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const body = [
      "Chcę umówić rozmowę o Agencie OZE dla firmy.",
      "",
      `Imię i nazwisko: ${form.get("name") ?? ""}`,
      `Firma: ${form.get("company") ?? ""}`,
      `Telefon: ${form.get("phone") ?? ""}`,
      `Email: ${form.get("email") ?? ""}`,
      `Liczba handlowców: ${form.get("teamSize") ?? ""}`,
      "",
      "Wiadomość:",
      `${form.get("message") ?? ""}`,
    ].join("\n");

    window.location.href = `mailto:${contactEmail}?subject=${encodeURIComponent(
      "Agent OZE dla firmy - rozmowa",
    )}&body=${encodeURIComponent(body)}`;
    setSubmitted(true);
  }

  return (
    <form
      id="formularz"
      onSubmit={handleSubmit}
      style={{
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 8,
        background: "rgba(5,8,7,0.72)",
        boxShadow: "0 24px 80px rgba(0,0,0,0.45)",
        padding: 24,
        backdropFilter: "blur(14px)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <video
        src="/media/hero-bg.mp4"
        muted
        playsInline
        autoPlay
        loop
        preload="metadata"
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: 0.22,
          filter: "hue-rotate(70deg) saturate(1.55) contrast(1.05) brightness(0.82)",
          pointerEvents: "none",
        }}
      />
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.72), rgba(0,0,0,0.6)), radial-gradient(circle at 50% 10%, rgba(61,255,122,0.06), transparent 45%)",
          pointerEvents: "none",
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>
        <h2
          style={{
            margin: "0 0 20px",
            fontSize: 26,
            lineHeight: 1.15,
            color: "#fff",
            textWrap: "balance" as CSSProperties["textWrap"],
          }}
        >
          Może będziemy mogli zautomatyzować inne procesy w firmie.
        </h2>

        <div style={{ display: "grid", gap: 14 }}>
          <Field label="Imię i nazwisko" name="name" autoComplete="name" />
          <Field label="Firma" name="company" autoComplete="organization" />
          <Field label="Telefon" name="phone" type="tel" autoComplete="tel" />
          <Field label="Email" name="email" type="email" autoComplete="email" />
          <label style={{ display: "grid", gap: 8, color: "rgba(255,255,255,0.82)", fontSize: 14 }}>
            Liczba handlowców
            <select
              required
              name="teamSize"
              style={inputStyle}
              defaultValue=""
            >
              <option value="" disabled>
                Wybierz
              </option>
              <option>1-3</option>
              <option>4-8</option>
              <option>9-20</option>
              <option>21+</option>
            </select>
          </label>
          <label style={{ display: "grid", gap: 8, color: "rgba(255,255,255,0.82)", fontSize: 14 }}>
            Wiadomość
            <textarea
              required
              name="message"
              rows={4}
              placeholder="Napisz krótko, co chcesz zautomatyzować."
              style={{
                ...inputStyle,
                resize: "vertical",
                minHeight: 112,
                lineHeight: 1.5,
              }}
            />
          </label>
        </div>

        <button
          type="submit"
          style={{
            width: "100%",
            height: 52,
            border: 0,
            borderRadius: 999,
            background: "#3DFF7A",
            color: "#000",
            fontWeight: 800,
            fontSize: 15,
            marginTop: 18,
            cursor: "pointer",
            boxShadow: "0 10px 28px rgba(0,0,0,0.34)",
          }}
        >
          Umów się na rozmowę
        </button>

        <a
          href={socialUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-flex",
            marginTop: 14,
            color: "#3DFF7A",
            fontSize: 13,
            fontWeight: 700,
            textDecoration: "none",
          }}
        >
          Social media →
        </a>

        {submitted ? (
          <p
            style={{
              margin: "14px 0 0",
              color: "rgba(255,255,255,0.72)",
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            Otworzyliśmy gotowego maila. Jeśli nic się nie stało, napisz na{" "}
            {contactEmail}.
          </p>
        ) : null}
      </div>
    </form>
  );
}

function Field({
  label,
  name,
  type = "text",
  autoComplete,
}: {
  label: string;
  name: string;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <label style={{ display: "grid", gap: 8, color: "rgba(255,255,255,0.82)", fontSize: 14 }}>
      {label}
      <input
        required
        name={name}
        type={type}
        autoComplete={autoComplete}
        style={inputStyle}
      />
    </label>
  );
}

const inputStyle = {
  width: "100%",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 8,
  background: "rgba(0,0,0,0.42)",
  color: "#fff",
  padding: "13px 14px",
  fontSize: 15,
  outline: "none",
} as const;
