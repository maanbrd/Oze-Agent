"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const G = "#3DFF7A"; // bright OZE green from cinematic hero design
const VOICE_WAVE_HEIGHTS = [3, 9, 12, 7, 5, 11, 8, 4, 10, 12, 6, 5, 9, 11, 7];

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    const update = () => setMatches(media.matches);

    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [query]);

  return matches;
}

export function Landing() {
  return (
    <div style={{ minHeight: "100vh", background: "#000", color: "#fff", overflow: "hidden" }}>
      <LandingNav />
      <CinematicHero />
      <BrandStrip />
      <PathSection />
      <ConversationDemo />
      <PricingSection />
      <DataPromise />
      <FAQSection />
      <FinalCTA />
      <FooterMin />
    </div>
  );
}

// ── NAV ───────────────────────────────────────────────────────────────────
function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const compact = useMediaQuery("(max-width: 920px)");
  const mobile = useMediaQuery("(max-width: 560px)");

  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 24);
    f();
    window.addEventListener("scroll", f);
    return () => window.removeEventListener("scroll", f);
  }, []);
  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        background: scrolled ? "rgba(0,0,0,0.78)" : "transparent",
        backdropFilter: scrolled ? "blur(14px)" : "none",
        WebkitBackdropFilter: scrolled ? "blur(14px)" : "none",
        borderBottom: scrolled ? "1px solid rgba(255,255,255,0.06)" : "1px solid transparent",
        transition: "all .3s",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: mobile ? "16px 20px" : "20px 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: mobile ? 12 : 28,
        }}
      >
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "#fff" }}>
          <RingLogo />
          <span style={{ fontWeight: 600, fontSize: 17, whiteSpace: "nowrap" }}>
            OZE Agent
          </span>
        </Link>
        <nav style={{ display: compact ? "none" : "flex", gap: 4, marginLeft: 32, flex: 1 }}>
          {(
            [
              ["jak działa", "#jak-dziala"],
              ["co umie agent", "#demo"],
              ["cennik", "#cennik"],
              ["faq", "#faq"],
              ["kontakt", "#kontakt"],
            ] as const
          ).map(([label, href]) => (
            <a
              key={label}
              href={href}
              style={{
                padding: "8px 14px",
                fontSize: 14,
                color: "rgba(255,255,255,0.75)",
                borderRadius: 6,
                transition: "color .15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.75)")}
            >
              {label}
            </a>
          ))}
        </nav>
        <Link
          href="/login"
          style={{
            display: compact ? "none" : "inline-flex",
            background: "transparent",
            border: 0,
            color: "rgba(255,255,255,0.85)",
            fontSize: 14,
            padding: "8px 14px",
            textDecoration: "none",
          }}
        >
          zaloguj
        </Link>
        <Link
          href="/rejestracja"
          style={{
            height: mobile ? 38 : 40,
            padding: mobile ? "0 14px" : "0 18px",
            borderRadius: 999,
            background: G,
            color: "#000",
            fontWeight: 700,
            fontSize: mobile ? 13 : 14,
            border: 0,
            boxShadow: `0 0 24px ${G}55`,
            display: mobile ? "none" : "inline-flex",
            alignItems: "center",
            whiteSpace: "nowrap",
            textDecoration: "none",
          }}
        >
          załóż konto
        </Link>
      </div>
    </header>
  );
}

function RingLogo() {
  return (
    <div
      style={{
        width: 32,
        height: 32,
        borderRadius: "50%",
        position: "relative",
        border: `2.5px solid ${G}`,
        boxShadow: `0 0 16px ${G}66, inset 0 0 8px ${G}33`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: G,
          boxShadow: `0 0 8px ${G}`,
        }}
      />
    </div>
  );
}

// ── HERO ──────────────────────────────────────────────────────────────────
function CinematicHero() {
  const [hasVideo, setHasVideo] = useState(true); // assume yes; flips off on error
  const [videoReady, setVideoReady] = useState(false);
  const compact = useMediaQuery("(max-width: 860px)");
  const tablet = useMediaQuery("(max-width: 1080px)");
  const reduceMotion = useMediaQuery("(prefers-reduced-motion: reduce)");
  const showVideo = hasVideo && !reduceMotion;

  return (
    <section
      style={{
        position: "relative",
        minHeight: compact ? "auto" : "100vh",
        paddingTop: compact ? 76 : 96,
        overflow: "hidden",
      }}
    >
      {showVideo && (
        <video
          src="/media/hero-bg.mp4"
          muted
          playsInline
          autoPlay
          loop
          preload="metadata"
          aria-hidden="true"
          onCanPlay={() => setVideoReady(true)}
          onError={() => setHasVideo(false)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity: videoReady ? 0.7 : 0,
            transition: "opacity .4s ease",
            filter: "hue-rotate(70deg) saturate(1.6) contrast(1.05) brightness(0.85)",
          }}
        />
      )}
      {/* tint over video / fallback */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0) 28%, rgba(0,0,0,0) 65%, rgba(0,0,0,0.95) 100%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 25% 50%, rgba(61,255,122,0.1) 0%, transparent 55%)`,
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "relative",
          zIndex: 10,
          maxWidth: 1280,
          margin: "0 auto",
          padding: compact ? "64px 24px 56px" : tablet ? "40px 32px 72px" : "40px 40px 80px",
          display: "grid",
          gridTemplateColumns: compact ? "1fr" : tablet ? "0.95fr 0.82fr" : "1.05fr 1fr",
          gap: compact ? 34 : tablet ? 36 : 60,
          alignItems: "center",
          minHeight: compact ? "auto" : "calc(100vh - 96px)",
        }}
      >
        {/* Left: copy */}
        <div>
          <h1
            style={{
              fontSize: compact ? "clamp(40px, 12vw, 54px)" : "clamp(44px, 5.4vw, 76px)",
              lineHeight: 1.05,
              fontWeight: 600,
              margin: "0 0 28px",
              maxWidth: compact ? 360 : 720,
            }}
          >
            <span style={{ display: "block" }}>
              Skup Się{compact ? <br /> : " "}na Sprzedaży,
            </span>
            <span style={{ display: "block", color: G, textShadow: `0 0 40px ${G}44` }}>
              resztę robi{compact ? <br /> : " "}AgentOZE.
            </span>
          </h1>
          <p
            style={{
              fontSize: "clamp(16px, 1.4vw, 19px)",
              lineHeight: 1.5,
              color: "rgba(255,255,255,0.8)",
              maxWidth: 520,
              margin: "0 0 36px",
            }}
          >
            Klient w arkuszu, spotkanie w kalendarzu,
            <br />
            follow-up pilnowany. Bez klikania w Excelu.
          </p>
          <div
            style={{
              display: "flex",
              gap: 12,
              flexWrap: "wrap",
              alignItems: compact ? "stretch" : "center",
            }}
          >
            <Link
              href="/rejestracja"
              style={{
                height: 56,
                padding: "0 28px",
                borderRadius: 999,
                background: G,
                color: "#000",
                fontWeight: 700,
                fontSize: 15.5,
                border: 0,
                boxShadow: `0 0 28px ${G}55, 0 8px 24px rgba(0,0,0,0.4)`,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                textDecoration: "none",
              }}
            >
              Zacznij — 3 minuty
            </Link>
            <a
              href="#demo"
              style={{
                height: 56,
                padding: "0 26px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.04)",
                color: "#fff",
                fontWeight: 600,
                fontSize: 15.5,
                border: "1.5px solid rgba(255,255,255,0.5)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                textDecoration: "none",
              }}
            >
              Zobacz demo
            </a>
          </div>
        </div>
        {/* Right: phone */}
        <div style={{ display: "flex", justifyContent: "center", overflow: "hidden" }}>
          <HeroPhone compact={compact} />
        </div>
      </div>
    </section>
  );
}

function HeroPhone({ compact = false }: { compact?: boolean }) {
  return (
    <div
      style={{
        width: compact ? "min(310px, calc(100vw - 48px))" : 340,
        position: "relative",
        borderRadius: compact ? 40 : 48,
        padding: compact ? 7 : 9,
        background: "linear-gradient(160deg, #2a2d33 0%, #0a0c0f 60%)",
        boxShadow: `0 30px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.06), 0 0 60px ${G}25`,
        transform: compact ? "rotate(0deg)" : "rotate(2deg)",
      }}
    >
      <div
        style={{
          background: "#0E1216",
          borderRadius: compact ? 34 : 40,
          overflow: "hidden",
          height: compact ? 590 : 660,
          display: "flex",
          flexDirection: "column",
          position: "relative",
        }}
      >
        {/* Status bar */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "14px 26px 6px",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          <span>11:37</span>
          <div
            style={{
              position: "absolute",
              top: 12,
              left: "50%",
              transform: "translateX(-50%)",
              width: 92,
              height: 28,
              borderRadius: 14,
              background: "#000",
            }}
          />
          <div style={{ display: "flex", gap: 5, alignItems: "center", fontSize: 11 }}>
            <span>●●●●</span>
            <span>📶</span>
            <span>🔋</span>
          </div>
        </div>
        {/* Telegram header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "14px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13.5,
              color: "rgba(255,255,255,0.7)",
            }}
          >
            <span style={{ fontSize: 14 }}>‹</span> Chats
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 14.5, fontWeight: 600 }}>@OZEAgentBot</div>
            <div style={{ fontSize: 10.5, color: "rgba(255,255,255,0.45)" }}>bot</div>
          </div>
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 15,
              border: `2px solid ${G}`,
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 5,
                borderRadius: 10,
                background: G,
                boxShadow: `0 0 8px ${G}`,
              }}
            />
          </div>
        </div>
        {/* Chat */}
        <div
          style={{
            flex: 1,
            padding: "14px 12px",
            display: "flex",
            flexDirection: "column",
            gap: 8,
            fontSize: 12.5,
          }}
        >
          <div
            style={{
              alignSelf: "center",
              fontSize: 11,
              color: "rgba(255,255,255,0.4)",
              padding: "4px 10px",
              borderRadius: 10,
              background: "rgba(255,255,255,0.04)",
            }}
          >
            Dzisiaj
          </div>

          {/* User voice msg */}
          <div
            style={{
              alignSelf: "flex-end",
              background: G,
              color: "#000",
              padding: "10px 12px",
              borderRadius: 16,
              borderBottomRightRadius: 4,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span
              style={{
                width: 24,
                height: 24,
                borderRadius: 12,
                background: "rgba(0,0,0,0.18)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
              }}
            >
              🎙
            </span>
            <svg width="60" height="14" viewBox="0 0 60 14">
              <g fill="rgba(0,0,0,0.55)">
                {VOICE_WAVE_HEIGHTS.map((h, i) => {
                  return <rect key={i} x={i * 4} y={7 - h / 2} width="2" height={h} rx="1" />;
                })}
              </g>
            </svg>
            <span style={{ fontSize: 11, fontWeight: 600 }}>0:14</span>
            <span style={{ fontSize: 10, opacity: 0.6, marginLeft: 4 }}>11:36 ✓✓</span>
          </div>

          {/* Bot card */}
          <div
            style={{
              alignSelf: "flex-start",
              background: "#1B1F23",
              color: "#fff",
              padding: "12px 14px",
              borderRadius: 16,
              borderBottomLeftRadius: 4,
              maxWidth: "88%",
              lineHeight: 1.5,
            }}
          >
            <div
              style={{
                fontSize: 12.5,
                fontWeight: 600,
                marginBottom: 6,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              📋 Jan Kowalski, Warszawa
            </div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.78)" }}>
              Produkt: PV
              <br />
              Tel. 600 123 456
              <br />
              <span style={{ display: "block", marginTop: 4 }}>
                Notatki: dom 160m², dach 40m² płd., zainteresowany ofertą
              </span>
            </div>
            <div
              style={{
                marginTop: 8,
                fontSize: 11.5,
                color: G,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span>📅</span> 18.04.2026 (Sobota) — follow-up
            </div>
            <div
              style={{
                marginTop: 4,
                fontSize: 11.5,
                color: "#FFB84D",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span>?</span> Brakuje: źródło leada
            </div>
            <div
              style={{
                textAlign: "right",
                fontSize: 9.5,
                color: "rgba(255,255,255,0.4)",
                marginTop: 4,
              }}
            >
              11:37
            </div>
          </div>

          {/* Action buttons (under bot card) */}
          <div aria-hidden="true" style={{ alignSelf: "flex-start", display: "flex", gap: 6, marginLeft: 4 }}>
            <span
              style={{
                background: G,
                color: "#000",
                fontWeight: 700,
                fontSize: 11.5,
                padding: "7px 12px",
                borderRadius: 14,
                border: 0,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                cursor: "default",
              }}
            >
              ✓ Zapisać
            </span>
            <span
              style={{
                background: "#1B1F23",
                color: "#fff",
                fontSize: 11.5,
                padding: "7px 12px",
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.1)",
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                cursor: "default",
              }}
            >
              + Dopisać
            </span>
            <span
              style={{
                background: "#1B1F23",
                color: "#fff",
                fontSize: 11.5,
                padding: "7px 12px",
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.1)",
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                cursor: "default",
              }}
            >
              × Anulować
            </span>
          </div>
        </div>
        {/* Input */}
        <div
          style={{
            padding: "10px 14px 14px",
            borderTop: "1px solid rgba(255,255,255,0.05)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 16 }}>📎</span>
          <span style={{ flex: 1, fontSize: 13, color: "rgba(255,255,255,0.4)" }}>Message</span>
          <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 14 }}>😊</span>
          <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 16 }}>🎙</span>
        </div>
        {/* Home indicator */}
        <div
          style={{
            width: 130,
            height: 4,
            background: "#fff",
            borderRadius: 2,
            margin: "4px auto 8px",
          }}
        />
      </div>
    </div>
  );
}

// ── BRAND STRIP ───────────────────────────────────────────────────────────
function BrandStrip() {
  const items: { name: string; icon: React.ReactNode }[] = [
    { name: "Anthropic", icon: <AnthropicMark /> },
    { name: "OpenAI", icon: <OpenAIMark /> },
    { name: "Google\nSheets", icon: <SheetsMark /> },
    { name: "Google\nCalendar", icon: <CalendarMark /> },
    { name: "Google\nDrive", icon: <DriveMark /> },
    { name: "Telegram", icon: <TelegramMark /> },
  ];
  return (
    <section
      style={{
        background: "#000",
        borderTop: "1px solid rgba(255,255,255,0.05)",
        padding: "24px 0",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        {items.map((it) => (
          <div
            key={it.name}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "10px 18px",
              borderRadius: 12,
              background: "rgba(255,255,255,0.025)",
              border: "1px solid rgba(255,255,255,0.06)",
              minWidth: 150,
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {it.icon}
            </div>
            <span
              style={{
                fontSize: 13,
                fontWeight: 500,
                whiteSpace: "pre-line",
                lineHeight: 1.15,
              }}
            >
              {it.name}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function AnthropicMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="#fff" aria-hidden>
      <path d="M13.4 4h3.2L22 20h-3.4l-1.1-3h-5L11.4 20H8L13.4 4zm.5 9.7h3.2l-1.6-4.6-1.6 4.6zM2 4h3.2L10.6 20H7.2L6.1 17H1L0 20h-.4L5 4h-3z M5.6 13.7L4 9.1l-1.6 4.6h3.2z" />
    </svg>
  );
}
function OpenAIMark() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#fff" strokeWidth="1.6" aria-hidden>
      <path d="M22 10.5a5.5 5.5 0 0 0-7.5-5.1A5.5 5.5 0 0 0 5 8.4 5.5 5.5 0 0 0 2 13.5a5.5 5.5 0 0 0 7.5 5.1 5.5 5.5 0 0 0 9.5-3 5.5 5.5 0 0 0 3-5.1z" />
      <path d="M12 2v20M2 12h20" opacity="0.3" />
    </svg>
  );
}
function SheetsMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden>
      <rect x="4" y="3" width="16" height="18" rx="2" fill="#0F9D58" />
      <path
        d="M7 8h10M7 12h10M7 16h10M9 7v12M14 7v12"
        stroke="#fff"
        strokeWidth="1.2"
        fill="none"
      />
    </svg>
  );
}
function CalendarMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden>
      <rect x="4" y="5" width="16" height="15" rx="2" fill="#fff" />
      <rect x="4" y="5" width="16" height="4" fill="#1A73E8" />
      <text x="12" y="17" fontSize="9" textAnchor="middle" fill="#1A73E8" fontWeight="700">
        31
      </text>
    </svg>
  );
}
function DriveMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden>
      <path d="M9 4l7 12-3.5 6H5.5L2 16l7-12z" fill="#FFC107" />
      <path d="M16 4h-7L16 16h7L16 4z" fill="#1FA463" />
      <path d="M5.5 22h7l3.5-6H9L5.5 22z" fill="#4285F4" />
    </svg>
  );
}
function TelegramMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden>
      <circle cx="12" cy="12" r="10" fill="#229ED9" />
      <path
        d="M7 12.2l9.5-3.7c.4-.2.8.1.7.6l-1.6 7.5c-.1.5-.5.6-.9.4l-2.6-1.9-1.3 1.2c-.1.1-.3.2-.5.2l.2-2.7 4.8-4.4c.2-.2 0-.3-.3-.1l-6 3.8-2.6-.8c-.5-.2-.5-.5.1-.7z"
        fill="#fff"
      />
    </svg>
  );
}

// ── PATH SECTION ──────────────────────────────────────────────────────────
function PathSection() {
  const compact = useMediaQuery("(max-width: 860px)");

  return (
    <section
      id="jak-dziala"
      style={{ padding: compact ? "76px 24px 56px" : "120px 32px 80px", position: "relative" }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <SectionEyebrow>Setup w 3 minuty</SectionEyebrow>
        <SectionTitle>Trzy kroki — wszystko zostaje u&nbsp;Ciebie.</SectionTitle>
        <p
          style={{
            fontSize: 16,
            color: "rgba(255,255,255,0.55)",
            maxWidth: 640,
            margin: "12px 0 56px",
            lineHeight: 1.55,
          }}
        >
          Płacisz, łączysz konto Google, parujesz Telegrama. Twój arkusz, kalendarz i folder na
          materiały zakładamy w Twoim koncie Google — nie kopiujemy ich do siebie.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: compact ? "1fr" : "repeat(3, 1fr)", gap: 18 }}>
          <PathCard
            num="01"
            title="Załóż konto i opłać"
            body="Imię, email, hasło. Wybierasz plan (49 zł/mies lub 350 zł/rok). Aktywacja 199 zł jednorazowo."
            cta="Zacznij"
            href="/rejestracja"
          >
            <BuyVisual />
          </PathCard>
          <PathCard
            num="02"
            title="Połącz Google"
            body="OAuth do Sheets, Calendar i Drive. Tworzymy arkusz „OZE Klienci 2026”, kalendarz „OZE Spotkania” i folder na materiały."
            cta="Pokaż jak"
            href="/rejestracja"
          >
            <GoogleVisual />
          </PathCard>
          <PathCard
            num="03"
            title="Sparuj Telegrama"
            body="Otwierasz @OZEAgentBot, wpisujesz kod 6-cyfrowy. Gotowe — agent słucha Twoich głosówek."
            cta="Sparuj"
            href="/rejestracja"
          >
            <TelegramVisual />
          </PathCard>
        </div>
      </div>
    </section>
  );
}

function PathCard({
  num,
  title,
  body,
  children,
  cta,
  href,
}: {
  num: string;
  title: string;
  body: string;
  children: React.ReactNode;
  cta: string;
  href: string;
}) {
  return (
    <div
      style={{
        borderRadius: 18,
        padding: 22,
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.08)",
        display: "flex",
        flexDirection: "column",
        gap: 16,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: 170,
          borderRadius: 12,
          background: "#000",
          border: "1px solid rgba(255,255,255,0.05)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {children}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <span className="num" style={{ fontSize: 13, color: G, fontWeight: 700 }}>
          {num}
        </span>
        <h3 style={{ fontSize: 19, fontWeight: 600, margin: 0 }}>
          {title}
        </h3>
      </div>
      <p
        style={{
          fontSize: 13.5,
          lineHeight: 1.55,
          color: "rgba(255,255,255,0.6)",
          margin: 0,
          flex: 1,
        }}
      >
        {body}
      </p>
      <Link
        href={href}
        style={{
          alignSelf: "flex-start",
          background: "transparent",
          border: 0,
          color: G,
          fontWeight: 600,
          fontSize: 13.5,
          padding: 0,
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          textDecoration: "none",
        }}
      >
        {cta} <span>→</span>
      </Link>
    </div>
  );
}

function BuyVisual() {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        padding: 18,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          color: "rgba(255,255,255,0.55)",
        }}
      >
        <span>Plan roczny</span>
        <span className="num" style={{ color: "#fff" }}>
          350 zł
        </span>
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          color: "rgba(255,255,255,0.55)",
        }}
      >
        <span>Aktywacja</span>
        <span className="num" style={{ color: "#fff" }}>
          199 zł
        </span>
      </div>
      <div style={{ height: 1, background: "rgba(255,255,255,0.08)", margin: "4px 0" }} />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        <span>Dziś</span>
        <span className="num" style={{ color: G }}>
          549 zł
        </span>
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
        {(["BLIK", "Karta", "Przelew"] as const).map((p) => (
          <div
            key={p}
            style={{
              flex: 1,
              padding: "8px 4px",
              textAlign: "center",
              fontSize: 11,
              borderRadius: 6,
              background: p === "BLIK" ? `${G}22` : "rgba(255,255,255,0.04)",
              color: p === "BLIK" ? G : "rgba(255,255,255,0.6)",
              border: `1px solid ${p === "BLIK" ? `${G}55` : "rgba(255,255,255,0.06)"}`,
            }}
          >
            {p}
          </div>
        ))}
      </div>
    </div>
  );
}

function GoogleVisual() {
  const items = [
    { mark: <SheetsMark />, name: "OZE Klienci 2026", kind: "Sheets" },
    { mark: <CalendarMark />, name: "OZE Spotkania", kind: "Calendar" },
    { mark: <DriveMark />, name: "Zdjęcia klientów", kind: "Drive" },
  ];
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        padding: 14,
        display: "flex",
        flexDirection: "column",
        gap: 7,
      }}
    >
      <div
        style={{
          fontSize: 10.5,
          color: "rgba(255,255,255,0.4)",
          textTransform: "uppercase",
          marginBottom: 4,
        }}
      >
        Tworzymy na Twoim Google
      </div>
      {items.map((it, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 10px",
            borderRadius: 8,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.05)",
            fontSize: 12.5,
          }}
        >
          <span style={{ width: 18, height: 18, display: "flex" }}>{it.mark}</span>
          <span style={{ flex: 1 }}>{it.name}</span>
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>{it.kind}</span>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: 7,
              background: G,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#000",
              fontSize: 9,
              fontWeight: 700,
            }}
          >
            ✓
          </span>
        </div>
      ))}
    </div>
  );
}

function TelegramVisual() {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 10,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          fontSize: 10.5,
          color: "rgba(255,255,255,0.4)",
          textTransform: "uppercase",
        }}
      >
        Twój kod parujący
      </div>
      <div
        className="num"
        style={{
          fontSize: 38,
          fontWeight: 700,
          color: G,
          fontVariantNumeric: "tabular-nums",
          textShadow: `0 0 20px ${G}55`,
        }}
      >
        3 9 2 1 7 4
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 11,
          color: "rgba(255,255,255,0.5)",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: 3,
            background: G,
            animation: "pulseDot 1.4s infinite",
          }}
        />
        Czekam na @OZEAgentBot
      </div>
    </div>
  );
}

// ── CONVERSATION DEMO ─────────────────────────────────────────────────────
function ConversationDemo() {
  const compact = useMediaQuery("(max-width: 860px)");
  const cards: [string, string, string][] = [
    [
      "🎙️",
      "Głosówka i tekst",
      'Agent rozumie polskie odmiany („u Krzywińskim" → Krzywiński).',
    ],
    [
      "📅",
      "Kalendarz dodaje się sam",
      '„Jutro o 14 jadę do Kowalskiego" → wydarzenie w kalendarzu.',
    ],
    ["🫡", "Poranny brief o 7:00", '„Dziś masz 4 spotkania. 2 wymagają potwierdzenia."'],
  ];
  return (
    <section
      id="demo"
      style={{ padding: "80px 32px", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <SectionEyebrow center>Co umie agent</SectionEyebrow>
        <SectionTitle center>
          Mówisz po polsku.
          <br />
          Agent rozumie i pisze.
        </SectionTitle>
        <p
          style={{
            fontSize: 16,
            color: "rgba(255,255,255,0.6)",
            maxWidth: 600,
            margin: "20px auto 60px",
            lineHeight: 1.6,
            textAlign: "center",
          }}
        >
          Po spotkaniu wysyłasz głosówkę. Agent wyciąga imię, miasto, telefon, produkt i pyta o
          brakujące rzeczy. Ty potwierdzasz — wpada do arkusza i kalendarza.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: compact ? "1fr" : "repeat(3, 1fr)", gap: 18 }}>
          {cards.map(([ic, t, b]) => (
            <div
              key={t}
              style={{
                padding: 24,
                borderRadius: 16,
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: `${G}18`,
                  border: `1px solid ${G}44`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 20,
                  marginBottom: 16,
                }}
              >
                {ic}
              </div>
              <div style={{ fontSize: 16.5, fontWeight: 600, marginBottom: 8 }}>{t}</div>
              <div
                style={{
                  fontSize: 13.5,
                  color: "rgba(255,255,255,0.55)",
                  lineHeight: 1.55,
                }}
              >
                {b}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── PRICING ───────────────────────────────────────────────────────────────
function PricingSection() {
  const compact = useMediaQuery("(max-width: 760px)");
  const plans = [
    {
      name: "Miesięcznie",
      price: "49 zł",
      sub: "/ mies",
      desc: "Płacisz co miesiąc, rezygnujesz kiedy chcesz.",
      features: [
        "Pełny dostęp do agenta",
        "Web app — wszystkie funkcje",
        "Poranny brief w Telegramie",
        "Faktura VAT",
      ],
      best: false,
    },
    {
      name: "Rocznie",
      price: "350 zł",
      sub: "/ rok",
      desc: "2 miesiące gratis. Najczęściej wybierane.",
      features: [
        "Wszystko z planu miesięcznego",
        "Oszczędzasz 238 zł",
        "Priorytetowy support",
        "Faktura VAT",
      ],
      best: true,
    },
  ];
  return (
    <section
      id="cennik"
      style={{ padding: "100px 32px 80px", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <SectionEyebrow center>Cennik</SectionEyebrow>
          <SectionTitle center>Aktywacja jednorazowo + plan.</SectionTitle>
          <p
            style={{
              fontSize: 15,
              color: "rgba(255,255,255,0.55)",
              maxWidth: 540,
              margin: "12px auto 0",
            }}
          >
            Aktywacja 199 zł obejmuje setup arkusza, kalendarza, folderu i parowanie z Telegramem.
          </p>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: compact ? "1fr" : "repeat(2, 1fr)",
            gap: 16,
            maxWidth: 760,
            margin: "0 auto",
          }}
        >
          {plans.map((p) => (
            <div
              key={p.name}
              style={{
                padding: 28,
                borderRadius: 16,
                background: p.best
                  ? `linear-gradient(180deg, ${G}10, ${G}03)`
                  : "rgba(255,255,255,0.025)",
                border: `1px solid ${p.best ? `${G}55` : "rgba(255,255,255,0.08)"}`,
                position: "relative",
              }}
            >
              {p.best && (
                <div
                  style={{
                    position: "absolute",
                    top: -10,
                    right: 20,
                    background: G,
                    color: "#000",
                    fontSize: 10.5,
                    fontWeight: 700,
                    padding: "4px 10px",
                    borderRadius: 999,
                    textTransform: "uppercase",
                  }}
                >
                  Polecane
                </div>
              )}
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.55)", marginBottom: 8 }}>
                {p.name}
              </div>
              <div
                style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 8 }}
              >
                <span
                  className="num"
                  style={{ fontSize: 44, fontWeight: 600 }}
                >
                  {p.price}
                </span>
                <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 14 }}>{p.sub}</span>
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: "rgba(255,255,255,0.65)",
                  marginBottom: 22,
                  minHeight: 38,
                }}
              >
                {p.desc}
              </div>
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: "0 0 24px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                }}
              >
                {p.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      display: "flex",
                      gap: 10,
                      fontSize: 13.5,
                      color: "rgba(255,255,255,0.75)",
                    }}
                  >
                    <span style={{ color: G, flexShrink: 0 }}>✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/rejestracja"
                style={{
                  width: "100%",
                  height: 44,
                  borderRadius: 999,
                  background: p.best ? G : "transparent",
                  color: p.best ? "#000" : "#fff",
                  border: p.best ? "0" : "1px solid rgba(255,255,255,0.18)",
                  fontWeight: 700,
                  fontSize: 14,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  textDecoration: "none",
                }}
              >
                Wybierz {p.name.toLowerCase()}
              </Link>
            </div>
          ))}
        </div>
        <div
          style={{
            textAlign: "center",
            marginTop: 28,
            fontSize: 12.5,
            color: "rgba(255,255,255,0.4)",
          }}
        >
          Aktywacja 199 zł doliczona przy pierwszej płatności. BLIK, karta, przelew (Przelewy24).
        </div>
      </div>
    </section>
  );
}

// ── DATA PROMISE ──────────────────────────────────────────────────────────
function DataPromise() {
  const compact = useMediaQuery("(max-width: 760px)");
  const items = [
    { mark: <SheetsMark />, t: "Sheets", b: "Twój arkusz, 16 kolumn, 9 statusów." },
    { mark: <CalendarMark />, t: "Calendar", b: 'Dedykowany kalendarz „OZE Spotkania".' },
    { mark: <DriveMark />, t: "Drive", b: "Folder na materiały i zdjęcia klienta." },
  ];
  return (
    <section
      id="dane"
      style={{ padding: "80px 32px", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      <div style={{ maxWidth: 980, margin: "0 auto", textAlign: "center" }}>
        <SectionEyebrow center>Twoje dane</SectionEyebrow>
        <SectionTitle center>
          Klienci żyją w&nbsp;<span style={{ color: G }}>Twoim Google</span>,
          <br />
          nie w naszej bazie.
        </SectionTitle>
        <p
          style={{
            fontSize: 16,
            color: "rgba(255,255,255,0.6)",
            maxWidth: 720,
            margin: "20px auto 40px",
            lineHeight: 1.6,
          }}
        >
          Arkusz, kalendarz i zdjęcia powstają na Twoim koncie Google. Możesz je w każdej chwili
          otworzyć ręcznie. Jeśli rezygnujesz — agent przestaje działać, ale Twoja baza zostaje u
          Ciebie.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: compact ? "1fr" : "repeat(3, 1fr)",
            gap: 16,
            maxWidth: 720,
            margin: "0 auto",
          }}
        >
          {items.map((it) => (
            <div
              key={it.t}
              style={{
                padding: 22,
                borderRadius: 12,
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.06)",
                textAlign: "left",
              }}
            >
              <div style={{ width: 32, height: 32, marginBottom: 10, display: "flex" }}>
                {it.mark}
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{it.t}</div>
              <div
                style={{
                  fontSize: 12.5,
                  color: "rgba(255,255,255,0.55)",
                  lineHeight: 1.5,
                }}
              >
                {it.b}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── FAQ ───────────────────────────────────────────────────────────────────
function FAQSection() {
  const items = [
    {
      q: "Gdzie są moje dane klientów?",
      a: "Na Twoim koncie Google — w Twoich Sheets, Calendar i Drive. Nic nie kopiujemy do siebie.",
    },
    {
      q: "Co jeśli zrezygnuję?",
      a: "Dane zostają na Twoim koncie Google. Nic nie kasujemy. Agent przestaje słuchać, dopóki nie wznowisz subskrypcji.",
    },
    {
      q: "Czy agent rozumie polskie odmiany?",
      a: "„U Krzywińskim”, „Kowalskiej”, „pojechałem do Wójcika” — agent rozpoznaje formy gramatyczne i zapisuje mianownik.",
    },
    {
      q: "Czy muszę kupować nowe konto Google?",
      a: "Zalecamy osobne konto OZE (15 GB Drive za darmo, oddzielone od prywatnych plików), ale to nie jest wymagane.",
    },
    {
      q: "Czy faktura VAT jest dostępna?",
      a: "Tak. Wszystkie faktury z NIP-em znajdziesz w sekcji Płatności w panelu.",
    },
    {
      q: "Czemu Telegram, a nie aplikacja?",
      a: "Telegram jest do pracy w terenie — głosówki w aucie. Web app jest do przeglądu przy biurku. Dwa kanały, jeden produkt.",
    },
  ];
  const [open, setOpen] = useState<number>(0);
  return (
    <section
      id="faq"
      style={{ padding: "80px 32px", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        <SectionEyebrow center>FAQ</SectionEyebrow>
        <SectionTitle center>Najczęstsze pytania.</SectionTitle>
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 6 }}>
          {items.map((f, i) => (
            <div
              key={i}
              style={{
                borderRadius: 12,
                background: open === i ? "rgba(255,255,255,0.04)" : "transparent",
                border: `1px solid ${open === i ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)"}`,
                transition: "all .2s",
              }}
            >
              <button
                type="button"
                aria-expanded={open === i}
                aria-controls={`faq-panel-${i}`}
                onClick={() => setOpen(open === i ? -1 : i)}
                style={{
                  width: "100%",
                  padding: "18px 22px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  background: "transparent",
                  border: 0,
                  cursor: "pointer",
                  color: "#fff",
                  fontFamily: "inherit",
                  fontSize: 15,
                  fontWeight: 500,
                  textAlign: "left",
                }}
              >
                <span>{f.q}</span>
                <span
                  style={{
                    color: open === i ? G : "rgba(255,255,255,0.4)",
                    transform: open === i ? "rotate(45deg)" : "none",
                    transition: "transform .2s",
                    fontSize: 18,
                  }}
                >
                  +
                </span>
              </button>
              {open === i && (
                <div
                  id={`faq-panel-${i}`}
                  style={{
                    padding: "0 22px 20px",
                    fontSize: 14,
                    color: "rgba(255,255,255,0.65)",
                    lineHeight: 1.65,
                  }}
                >
                  {f.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── FINAL CTA ─────────────────────────────────────────────────────────────
function FinalCTA() {
  return (
    <section
      id="kontakt"
      style={{ padding: "100px 32px", position: "relative", overflow: "hidden" }}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: 1000,
          height: 500,
          transform: "translate(-50%, -50%)",
          background: `radial-gradient(ellipse, ${G}22 0%, transparent 60%)`,
          filter: "blur(60px)",
          pointerEvents: "none",
        }}
      />
      <div style={{ maxWidth: 720, margin: "0 auto", textAlign: "center", position: "relative" }}>
        <h2
          style={{
            fontSize: "clamp(36px, 5vw, 64px)",
            lineHeight: 1.05,
            fontWeight: 600,
            margin: "0 0 20px",
          }}
        >
          Załóż konto
          <br />
          <span style={{ color: G }}>i zacznij dziś.</span>
        </h2>
        <p
          style={{
            fontSize: 16,
            color: "rgba(255,255,255,0.6)",
            maxWidth: 540,
            margin: "0 auto 32px",
            lineHeight: 1.55,
          }}
        >
          3 minuty setup. 549 zł dziś (aktywacja + roczny plan). Pierwszy klient wpada do arkusza
          jeszcze przed kolejnym spotkaniem.
        </p>
        <Link
          href="/rejestracja"
          style={{
            height: 60,
            padding: "0 32px",
            borderRadius: 999,
            background: G,
            color: "#000",
            fontWeight: 700,
            fontSize: 16,
            border: 0,
            boxShadow: `0 0 40px ${G}55, 0 12px 40px rgba(0,0,0,0.4)`,
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            textDecoration: "none",
          }}
        >
          Załóż konto <span>→</span>
        </Link>
        <div
          style={{
            marginTop: 16,
            fontSize: 12.5,
            color: "rgba(255,255,255,0.4)",
          }}
        >
          Bez umowy długoterminowej · Faktura VAT · BLIK / karta / przelew
        </div>
      </div>
    </section>
  );
}

// ── FOOTER ────────────────────────────────────────────────────────────────
function FooterMin() {
  const compact = useMediaQuery("(max-width: 760px)");

  return (
    <footer
      style={{
        borderTop: "1px solid rgba(255,255,255,0.05)",
        padding: "32px",
        background: "#000",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          display: "flex",
          flexDirection: compact ? "column" : "row",
          justifyContent: compact ? "flex-start" : "space-between",
          alignItems: compact ? "flex-start" : "center",
          flexWrap: "wrap",
          gap: 16,
          fontSize: 12,
          color: "rgba(255,255,255,0.4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <RingLogo />
          <span>© 2026 OZE Agent</span>
        </div>
        <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
          <Link href="/polityka-prywatnosci" style={{ color: "inherit" }}>
            Polityka prywatności
          </Link>
          <Link href="/regulamin" style={{ color: "inherit" }}>
            Regulamin
          </Link>
          <a href="#kontakt" style={{ color: "inherit" }}>
            Kontakt
          </a>
        </div>
      </div>
    </footer>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────
function SectionEyebrow({
  children,
  center,
}: {
  children: React.ReactNode;
  center?: boolean;
}) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        fontSize: 11.5,
        fontWeight: 600,
        textTransform: "uppercase",
        color: G,
        marginBottom: 12,
        width: center ? "100%" : "auto",
        justifyContent: center ? "center" : "flex-start",
      }}
    >
      <span style={{ width: 18, height: 1, background: G }} />
      {children}
    </div>
  );
}

function SectionTitle({
  children,
  center,
}: {
  children: React.ReactNode;
  center?: boolean;
}) {
  return (
    <h2
      style={{
        fontSize: "clamp(32px, 4.5vw, 56px)",
        lineHeight: 1.05,
        fontWeight: 600,
        margin: 0,
        textAlign: center ? "center" : "left",
        textWrap: "balance" as React.CSSProperties["textWrap"],
      }}
    >
      {children}
    </h2>
  );
}
