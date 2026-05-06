import Link from "next/link";

const G = "#3DFF7A";

export const metadata = {
  title: "Dla firm OZE — w przygotowaniu | OZE Agent",
  description:
    "Wersja Agenta OZE dla całych zespołów sprzedaży jest w przygotowaniu. Napisz na kontakt@oze-agent.pl, damy znać, kiedy będzie gotowa.",
};

export default function FirmaPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#000",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 32,
        textAlign: "center",
        gap: 18,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, ${G}10 0%, transparent 60%)`,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          fontSize: 12,
          color: G,
          textTransform: "uppercase",
          letterSpacing: 2,
          fontWeight: 700,
          position: "relative",
        }}
      >
        — Dla firm OZE
      </div>
      <h1
        style={{
          fontSize: "clamp(32px, 5vw, 56px)",
          fontWeight: 600,
          lineHeight: 1.1,
          margin: 0,
          maxWidth: 720,
          position: "relative",
          textWrap: "balance" as React.CSSProperties["textWrap"],
        }}
      >
        Strona dla właścicieli firm OZE
        <br />
        <span style={{ color: G, textShadow: `0 0 40px ${G}55` }}>w przygotowaniu.</span>
      </h1>
      <p
        style={{
          color: "rgba(255,255,255,0.65)",
          maxWidth: 560,
          lineHeight: 1.6,
          fontSize: 16,
          margin: 0,
          position: "relative",
        }}
      >
        Pracujemy nad wersją Agenta OZE dla całych zespołów sprzedaży. Napisz na{" "}
        <a
          href="mailto:kontakt@oze-agent.pl"
          style={{ color: G, textDecoration: "underline", textUnderlineOffset: 3 }}
        >
          kontakt@oze-agent.pl
        </a>
        , a damy znać, kiedy będzie gotowa.
      </p>
      <Link
        href="/"
        style={{
          marginTop: 12,
          padding: "14px 26px",
          borderRadius: 999,
          background: G,
          color: "#000",
          fontWeight: 700,
          fontSize: 14.5,
          textDecoration: "none",
          boxShadow: `0 0 28px ${G}55`,
          position: "relative",
        }}
      >
        ← Wróć na stronę główną
      </Link>
    </main>
  );
}
