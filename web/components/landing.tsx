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
      <TopBar />
      <LandingNav />
      <CinematicHero />
      <BrandStrip />
      <IleTraciszSection />
      <RozwiazanieSection />
      <DzienHandlowcaSection />
      <FunkcjeSection />
      <RezultatSection />
      <TwojeNarzedziaSection />
      <FAQSection />
      <FinalCTA />
      <FooterMin />
    </div>
  );
}

// ── TOP BAR ───────────────────────────────────────────────────────────────
function TopBar() {
  const [hover, setHover] = useState(false);
  const mobile = useMediaQuery("(max-width: 560px)");
  return (
    <Link
      href="/firma"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "block",
        background: hover ? "#0a0d10" : "#06080a",
        borderBottom: `1px solid ${G}2D`,
        padding: mobile ? "9px 14px" : "10px 16px",
        textAlign: "center",
        textDecoration: "none",
        color: "rgba(255,255,255,0.85)",
        fontSize: mobile ? 12 : 13,
        lineHeight: 1.4,
        transition: "background .15s",
        position: "relative",
        zIndex: 50,
      }}
    >
      <span aria-hidden="true" style={{ marginRight: 6 }}>🏢</span>
      {mobile ? (
        <>Właścicielu firmy OZE? Zobacz, co Agent robi dla zespołu →</>
      ) : (
        <>Jesteś właścicielem firmy OZE? Zobacz, co Agent OZE robi dla całego zespołu sprzedaży →</>
      )}
    </Link>
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
        position: "sticky",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        background: scrolled ? "rgba(0,0,0,0.78)" : "rgba(0,0,0,0.5)",
        backdropFilter: scrolled ? "blur(14px)" : "blur(6px)",
        WebkitBackdropFilter: scrolled ? "blur(14px)" : "blur(6px)",
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
              ["jak działa", "#dzien-handlowca"],
              ["co umie agent", "#funkcje"],
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
  const [hasVideo, setHasVideo] = useState(true);
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
        paddingTop: compact ? 12 : 24,
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
          gridTemplateColumns: compact ? "1fr" : tablet ? "minmax(0, 1fr) 360px" : "minmax(0, 1fr) 400px",
          gap: compact ? 34 : tablet ? 36 : 60,
          alignItems: "center",
          minHeight: compact ? "auto" : "calc(100vh - 96px)",
        }}
      >
        <div>
          <h1
            style={{
              fontSize: compact ? "clamp(36px, 11vw, 50px)" : "clamp(40px, 5vw, 70px)",
              lineHeight: 1.05,
              fontWeight: 600,
              margin: "0 0 28px",
              maxWidth: compact ? 420 : 900,
              textWrap: "balance" as React.CSSProperties["textWrap"],
            }}
          >
            <span style={{ display: "block" }}>Każdy zapomniany klient</span>
            <span style={{ display: "block" }}>
              to{" "}
              <span style={{ color: G, textShadow: `0 0 40px ${G}55` }}>5 000 – 10 000 zł</span>,
            </span>
            <span style={{ display: "block" }}>które właśnie wypłynęły</span>
            <span style={{ display: "block" }}>z Twojego konta.</span>
          </h1>
          <p
            style={{
              fontSize: "clamp(15px, 1.4vw, 19px)",
              lineHeight: 1.55,
              color: "rgba(255,255,255,0.8)",
              maxWidth: 540,
              margin: "0 0 36px",
            }}
          >
            Agent OZE pilnuje Twoich leadów, follow-upów, zdjęć i ofert
            w&nbsp;Telegramie. Żeby ciepły klient nie stygł, bo byłeś
            wykończony po spotkaniach.
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
                gap: 8,
                textDecoration: "none",
              }}
            >
              Zacznij pilnować leadów <span aria-hidden="true">→</span>
            </Link>
            <a
              href="#dzien-handlowca"
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
              Zobacz, jak to działa
            </a>
          </div>
        </div>
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
    { name: "Gmail", icon: <GmailMark /> },
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
              minWidth: 130,
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
function GmailMark() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden>
      <rect x="2" y="5" width="20" height="14" rx="2" fill="#fff" />
      <path d="M2 5h2v14H2V5z" fill="#C5221F" />
      <path d="M20 5h2v14h-2V5z" fill="#C5221F" />
      <path d="M2 5l10 7 10-7v3l-10 7L2 8V5z" fill="#EA4335" />
      <path d="M2 5h2l8 5.6L20 5h2L12 12 2 5z" fill="#B31412" opacity="0.85" />
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

// ── ILE TRACISZ ───────────────────────────────────────────────────────────
function IleTraciszSection() {
  const compact = useMediaQuery("(max-width: 860px)");
  const cards: { value: string; body: string }[] = [
    {
      value: "5 000 – 10 000 zł",
      body: "Tyle zarabiasz na jednym kliencie OZE. Tyle tracisz, kiedy jeden lead zniknie w notatkach.",
    },
    {
      value: "10+ leadów / miesiąc",
      body: "Średnio tyle kontaktów wypada z głowy solo handlowca: numer w SMS-ie, adres na kartce, „oddzwonię jutro”.",
    },
    {
      value: "45 minut / dzień",
      body: "Tyle wieczorem siedzisz w aucie i odtwarzasz z pamięci, kto co powiedział. Część szczegółów już uciekła.",
    },
  ];
  return (
    <section
      id="ile-tracisz"
      style={{
        padding: compact ? "76px 24px 72px" : "120px 32px 100px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
        position: "relative",
      }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <SectionEyebrow center>ILE TRACISZ</SectionEyebrow>
        <SectionTitle center>Policz, ile już wyparowało.</SectionTitle>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: compact ? "1fr" : "repeat(3, 1fr)",
            gap: 18,
            marginTop: 56,
          }}
        >
          {cards.map((c) => (
            <div
              key={c.value}
              style={{
                padding: 28,
                borderRadius: 18,
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.08)",
                display: "flex",
                flexDirection: "column",
                gap: 14,
              }}
            >
              <div
                className="num"
                style={{
                  fontSize: compact ? "clamp(28px, 7vw, 36px)" : "clamp(28px, 3.4vw, 44px)",
                  fontWeight: 700,
                  color: G,
                  textShadow: `0 0 24px ${G}33`,
                  lineHeight: 1.05,
                }}
              >
                {c.value}
              </div>
              <p
                style={{
                  fontSize: 14.5,
                  lineHeight: 1.6,
                  color: "rgba(255,255,255,0.78)",
                  margin: 0,
                }}
              >
                {c.body}
              </p>
            </div>
          ))}
        </div>

        <ChaosToWalletSVG />

        <p
          style={{
            margin: compact ? "32px auto 0" : "48px auto 0",
            maxWidth: 760,
            textAlign: "center",
            fontSize: compact ? 18 : "clamp(18px, 2vw, 24px)",
            lineHeight: 1.45,
            color: "rgba(255,255,255,0.92)",
            textWrap: "balance" as React.CSSProperties["textWrap"],
          }}
        >
          Wystarczy, że odzyskasz{" "}
          <span style={{ color: G, fontWeight: 700 }}>JEDNEGO klienta miesięcznie</span>,
          którego normalnie byś zgubił. Agent OZE zwraca się{" "}
          <span style={{ color: G, fontWeight: 700 }}>20 razy</span>.
        </p>
      </div>
    </section>
  );
}

function ChaosToWalletSVG() {
  const compact = useMediaQuery("(max-width: 760px)");
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        marginTop: compact ? 36 : 56,
      }}
      aria-label="Diagram pokazujący jak leady giną w SMS-ach, notatkach i papierowym kalendarzu, prowadząc do straty pieniędzy"
      role="img"
    >
      <style>{`
        @keyframes pulse-glow {
          0%, 100% { filter: drop-shadow(0 0 4px ${G}66); opacity: 0.95; }
          50%      { filter: drop-shadow(0 0 14px ${G}cc); opacity: 1; }
        }
        .wallet-pulse { animation: pulse-glow 2.4s ease-in-out infinite; transform-origin: center; }
        @keyframes flow-arrow {
          0%   { stroke-dashoffset: 14; }
          100% { stroke-dashoffset: 0; }
        }
        .flow-arrow { animation: flow-arrow 1.6s linear infinite; }
      `}</style>
      <svg
        viewBox="0 0 800 200"
        style={{ width: "100%", maxWidth: 800, height: "auto" }}
        fill="none"
        stroke={G}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* SMS phone (left) */}
        <g transform="translate(40, 60)" opacity="0.85">
          <rect x="0" y="0" width="60" height="90" rx="10" />
          <line x1="22" y1="6" x2="38" y2="6" strokeWidth="1.2" />
          <rect x="10" y="22" width="40" height="14" rx="3" strokeWidth="1.2" />
          <rect x="10" y="42" width="32" height="10" rx="3" strokeWidth="1.2" opacity="0.6" />
          <rect x="18" y="58" width="40" height="14" rx="3" strokeWidth="1.2" />
          <text x="30" y="86" fontSize="9" fill={G} stroke="none" textAnchor="middle">
            SMS
          </text>
        </g>

        {/* Sticky note (middle-left) */}
        <g transform="translate(180, 50)" opacity="0.85">
          <path d="M0 0 L70 0 L70 70 L60 90 L0 90 Z" />
          <line x1="10" y1="20" x2="58" y2="20" strokeWidth="1.2" opacity="0.7" />
          <line x1="10" y1="34" x2="48" y2="34" strokeWidth="1.2" opacity="0.7" />
          <line x1="10" y1="48" x2="54" y2="48" strokeWidth="1.2" opacity="0.7" />
          <line x1="10" y1="62" x2="40" y2="62" strokeWidth="1.2" opacity="0.7" />
          <text x="35" y="106" fontSize="9" fill={G} stroke="none" textAnchor="middle">
            karteczka
          </text>
        </g>

        {/* Notebook (middle-right) */}
        <g transform="translate(320, 56)" opacity="0.85">
          <rect x="0" y="0" width="80" height="84" rx="4" />
          <line x1="0" y1="14" x2="80" y2="14" strokeWidth="1.2" opacity="0.6" />
          <line x1="0" y1="28" x2="80" y2="28" strokeWidth="1.2" opacity="0.6" />
          <line x1="0" y1="42" x2="80" y2="42" strokeWidth="1.2" opacity="0.6" />
          <line x1="0" y1="56" x2="80" y2="56" strokeWidth="1.2" opacity="0.6" />
          <line x1="0" y1="70" x2="80" y2="70" strokeWidth="1.2" opacity="0.6" />
          <circle cx="6" cy="6" r="2" />
          <circle cx="6" cy="78" r="2" />
          <text x="40" y="100" fontSize="9" fill={G} stroke="none" textAnchor="middle">
            notes
          </text>
        </g>

        {/* Arrow flowing right */}
        <g transform="translate(430, 100)">
          <line
            className="flow-arrow"
            x1="0"
            y1="0"
            x2="160"
            y2="0"
            strokeWidth="2"
            strokeDasharray="8 6"
          />
          <path d="M156 -8 L172 0 L156 8" strokeWidth="2" />
          <text x="80" y="-12" fontSize="11" fill={G} stroke="none" textAnchor="middle" opacity="0.9">
            chaos
          </text>
          <text x="80" y="22" fontSize="11" fill={G} stroke="none" textAnchor="middle" opacity="0.9">
            → strata
          </text>
        </g>

        {/* Wallet with falling coins (right) */}
        <g className="wallet-pulse" transform="translate(640, 50)">
          <path d="M5 30 Q5 20 15 20 L95 20 Q105 20 105 30 L105 80 Q105 90 95 90 L15 90 Q5 90 5 80 Z" />
          <path d="M5 30 L95 30 Q105 30 105 40 L105 50 Q105 60 95 60 L80 60" strokeWidth="1.5" />
          <circle cx="86" cy="48" r="4" fill={G} stroke="none" />
          {/* Falling coins */}
          <g opacity="0.85">
            <circle cx="40" cy="6" r="6" />
            <text x="40" y="10" fontSize="8" fill={G} stroke="none" textAnchor="middle" fontWeight="700">
              zł
            </text>
          </g>
          <g opacity="0.55">
            <circle cx="58" cy="-2" r="5" />
          </g>
          <g opacity="0.4">
            <circle cx="22" cy="0" r="4" />
          </g>
          <text x="55" y="108" fontSize="9" fill={G} stroke="none" textAnchor="middle">
            uciekająca prowizja
          </text>
        </g>
      </svg>
    </div>
  );
}

// ── ROZWIĄZANIE ───────────────────────────────────────────────────────────
function RozwiazanieSection() {
  const compact = useMediaQuery("(max-width: 760px)");
  return (
    <section
      id="rozwiazanie"
      style={{
        padding: compact ? "72px 24px" : "120px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <div style={{ maxWidth: 920, margin: "0 auto", textAlign: "center" }}>
        <h2
          style={{
            fontSize: compact ? "clamp(34px, 9vw, 44px)" : "clamp(40px, 5vw, 68px)",
            lineHeight: 1.05,
            fontWeight: 600,
            margin: 0,
            textWrap: "balance" as React.CSSProperties["textWrap"],
          }}
        >
          Mówisz do Telegrama.
          <br />
          <span style={{ color: G, textShadow: `0 0 40px ${G}55` }}>Agent OZE</span> robi resztę.
        </h2>
        <p
          style={{
            marginTop: 28,
            fontSize: "clamp(15px, 1.4vw, 18px)",
            lineHeight: 1.65,
            color: "rgba(255,255,255,0.6)",
            maxWidth: 640,
            marginInline: "auto",
          }}
        >
          Klient, spotkanie, zdjęcia, oferta, follow-up — wszystko ląduje tam, gdzie powinno:
          w&nbsp;Twoim Google Sheets, Calendar, Drive i&nbsp;Gmailu.
        </p>
        <div
          style={{
            marginTop: 24,
            display: "flex",
            flexDirection: compact ? "column" : "row",
            gap: compact ? 6 : 18,
            justifyContent: "center",
            fontSize: compact ? 16 : 17,
            color: "rgba(255,255,255,0.95)",
            fontWeight: 500,
          }}
        >
          <span>Bez klikania.</span>
          <span style={{ color: "rgba(255,255,255,0.25)", display: compact ? "none" : "inline" }}>·</span>
          <span>Bez przepisywania.</span>
          <span style={{ color: "rgba(255,255,255,0.25)", display: compact ? "none" : "inline" }}>·</span>
          <span>Bez gubienia.</span>
        </div>
      </div>
    </section>
  );
}

// ── DZIEŃ HANDLOWCA ───────────────────────────────────────────────────────
type Scenario = {
  num: string;
  title: string;
  body: React.ReactNode;
  image: string;
  alt: string;
};

function DzienHandlowcaSection() {
  const compact = useMediaQuery("(max-width: 860px)");
  const scenarios: Scenario[] = [
    {
      num: "01",
      title: "18:40 wsiadasz do auta po trzecim spotkaniu",
      image: "scenariusz-01-auto",
      alt: "Mockup Telegrama z kartą klienta po spotkaniu - Agent OZE",
      body: (
        <>
          <p style={paraStyle}>
            Nagrywasz głosówkę: „Jan Kowalski, Warszawa, dom 160m², dach 40m² południe,
            zainteresowany ofertą, follow-up sobota.”
          </p>
          <p style={paraStyle}>
            Agent zamienia to w kartę klienta. Klikasz „Zapisać”. Klient w arkuszu,
            follow-up w kalendarzu. Koniec dnia roboczego.
          </p>
        </>
      ),
    },
    {
      num: "02",
      title: "7:00 poranna kawa w kuchni",
      image: "scenariusz-02-brief",
      alt: "Mockup Telegrama z porannym briefem spotkań - Agent OZE",
      body: (
        <>
          <p style={paraStyle}>
            Telegram pinguje: „Dziś masz 4 spotkania. 9:30 Kowalski, 11:00 Nowak,
            14:00 Wiśniewski, 16:30 Lewandowski.”
          </p>
          <p style={paraStyle}>
            Otwierasz dzień bez przeszukiwania kalendarza. Wiesz dokładnie, gdzie
            jedziesz i&nbsp;o&nbsp;której.
          </p>
        </>
      ),
    },
    {
      num: "03",
      title: "Po wizycie u klienta",
      image: "scenariusz-03-zdjecia",
      alt: "Mockup Telegrama z przypisywaniem zdjęć do klienta - Agent OZE",
      body: (
        <>
          <p style={paraStyle}>Wysyłasz 8 zdjęć dachu do Telegrama.</p>
          <p style={paraStyle}>
            Agent: „Do którego klienta? Kowalski, Nowak, czy nowy?”
          </p>
          <p style={paraStyle}>
            Klikasz „Kowalski”. Zdjęcia w folderze Drive, link w arkuszu, podpięte
            pod kartę klienta.
          </p>
        </>
      ),
    },
    {
      num: "04",
      title: "Oferta wychodzi od razu po spotkaniu",
      image: "scenariusz-04-oferta",
      alt: "Mockup Telegrama z generowaniem oferty PDF - Agent OZE",
      body: (
        <>
          <p style={paraStyle}>
            Wsiadasz do auta i&nbsp;nagrywasz głosówkę: „Oferta dla Kowalskiego, 8kW, magazyn 10kWh.”
          </p>
          <p style={paraStyle}>
            Agent generuje PDF, pokazuje podgląd, czeka na „Wyślij”. Klikasz — mail
            leci z&nbsp;Twojego Gmaila, zanim ruszysz na kolejne spotkanie.
          </p>
        </>
      ),
    },
  ];

  return (
    <section
      id="dzien-handlowca"
      style={{
        padding: compact ? "76px 24px" : "120px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <SectionEyebrow center>DZIEŃ HANDLOWCA Z AGENTEM OZE</SectionEyebrow>
        <SectionTitle center>
          Cztery sytuacje, w&nbsp;których normalnie tracisz klienta.
        </SectionTitle>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: compact ? 56 : 88,
            marginTop: compact ? 56 : 80,
          }}
        >
          {scenarios.map((s, i) => (
            <ScenarioRow key={s.num} scenario={s} reversed={i % 2 === 1} compact={compact} />
          ))}
        </div>
      </div>
    </section>
  );
}

const paraStyle: React.CSSProperties = {
  fontSize: 15.5,
  lineHeight: 1.65,
  color: "rgba(255,255,255,0.72)",
  margin: "0 0 14px",
};

function ScenarioRow({
  scenario,
  reversed,
  compact,
}: {
  scenario: Scenario;
  reversed: boolean;
  compact: boolean;
}) {
  const [hover, setHover] = useState(false);
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: compact ? "1fr" : "1fr 1fr",
        gap: compact ? 28 : 56,
        alignItems: "center",
      }}
    >
      <div style={{ order: compact || !reversed ? 1 : 2 }}>
        <div
          className="num"
          style={{
            fontSize: 56,
            fontWeight: 700,
            color: G,
            textShadow: `0 0 24px ${G}33`,
            lineHeight: 1,
            marginBottom: 18,
          }}
        >
          {scenario.num}
        </div>
        <h3
          style={{
            fontSize: compact ? 24 : "clamp(22px, 2.4vw, 30px)",
            fontWeight: 600,
            lineHeight: 1.2,
            margin: "0 0 18px",
            textWrap: "balance" as React.CSSProperties["textWrap"],
          }}
        >
          {scenario.title}
        </h3>
        <div>{scenario.body}</div>
      </div>
      <div
        style={{
          order: compact || !reversed ? 2 : 1,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <picture>
          <source srcSet={`/images/landing/${scenario.image}.webp`} type="image/webp" />
          <img
            src={`/images/landing/${scenario.image}.jpg`}
            alt={scenario.alt}
            loading="lazy"
            onMouseEnter={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
            style={{
              width: "100%",
              maxWidth: 480,
              aspectRatio: "1 / 1",
              borderRadius: 16,
              objectFit: "cover",
              border: "1px solid rgba(255,255,255,0.08)",
              boxShadow: hover
                ? `0 0 40px ${G}26, 0 16px 40px rgba(0,0,0,0.5)`
                : "0 16px 40px rgba(0,0,0,0.5)",
              transition: "box-shadow 0.3s ease",
            }}
          />
        </picture>
      </div>
    </div>
  );
}

// ── FUNKCJE ───────────────────────────────────────────────────────────────
function FunkcjeSection() {
  const compact = useMediaQuery("(max-width: 760px)");
  const tablet = useMediaQuery("(max-width: 1024px)");
  const items: { icon: string; title: string; body: string }[] = [
    {
      icon: "🎤",
      title: "Klient głosem albo tekstem",
      body: "W aucie, w terenie, między spotkaniami. Tak, jak Ci wygodnie.",
    },
    {
      icon: "📊",
      title: "Google Sheets prowadzi się sam",
      body: "Każdy klient z imieniem, telefonem, statusem i kolejnym krokiem. Bez Twojej ręki.",
    },
    {
      icon: "📅",
      title: "Spotkania w Google Calendar",
      body: "„Jutro o 14 jadę do Kowalskiego” → wydarzenie w kalendarzu. Bez klikania.",
    },
    {
      icon: "📸",
      title: "Zdjęcia w Google Drive",
      body: "Folder na klienta, link w arkuszu. Nigdy więcej szukania w galerii.",
    },
    {
      icon: "📄",
      title: "Generator ofert PDF",
      body: "Głosówka po spotkaniu → PDF → mail z Gmaila. Zanim ruszysz na kolejne.",
    },
    {
      icon: "☀️",
      title: "Poranny brief o 7:00",
      body: "Lista dzisiejszych spotkań z godzinami. W jednej wiadomości na Telegramie.",
    },
  ];
  const cols = compact ? "1fr" : tablet ? "repeat(2, 1fr)" : "repeat(3, 1fr)";
  return (
    <section
      id="funkcje"
      style={{
        padding: compact ? "76px 24px" : "120px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <SectionEyebrow center>FUNKCJE</SectionEyebrow>
        <SectionTitle center>Wszystko w&nbsp;jednym Telegramie.</SectionTitle>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: cols,
            gap: 18,
            marginTop: 56,
          }}
        >
          {items.map((it) => (
            <FeatureTile key={it.title} icon={it.icon} title={it.title} body={it.body} />
          ))}
        </div>
        <div style={{ marginTop: 40, display: "flex", justifyContent: "center" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 18px",
              borderRadius: 999,
              border: `1px solid ${G}55`,
              background: `${G}0F`,
              fontSize: 13,
            }}
          >
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1.2,
                textTransform: "uppercase",
                color: G,
              }}
            >
              WKRÓTCE
            </span>
            <span style={{ color: G }}>→</span>
            <span style={{ color: "#fff" }}>
              Automatyczne SMS-y do klientów z poziomu dashboardu
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

function FeatureTile({ icon, title, body }: { icon: string; title: string; body: string }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: 24,
        borderRadius: 16,
        background: "rgba(255,255,255,0.025)",
        border: `1px solid ${hover ? `${G}4D` : "rgba(255,255,255,0.08)"}`,
        transition: "border-color 0.2s ease, transform 0.2s ease",
        transform: hover ? "translateY(-2px)" : "translateY(0)",
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: `${G}1A`,
          border: `1px solid ${G}40`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          marginBottom: 18,
        }}
      >
        <span aria-hidden="true">{icon}</span>
      </div>
      <h3 style={{ fontSize: 17, fontWeight: 600, margin: "0 0 8px", color: "#fff" }}>
        {title}
      </h3>
      <p style={{ fontSize: 14, lineHeight: 1.55, color: "rgba(255,255,255,0.6)", margin: 0 }}>
        {body}
      </p>
    </div>
  );
}

// ── REZULTAT ──────────────────────────────────────────────────────────────
function RezultatSection() {
  const compact = useMediaQuery("(max-width: 760px)");
  const before = [
    "Notatki w 4 miejscach",
    "Klient czeka 3 dni na telefon",
    "Wieczór = odtwarzanie z pamięci",
  ];
  const after = [
    "Wszystko w jednym Telegramie",
    "Reagujesz w godzinach, nie dniach",
    "Wieczór = wolne",
  ];
  const wins: { title: string; body: string }[] = [
    {
      title: "Zero leadów zgubionych w telefonie.",
      body: "Każdy kontakt ma miejsce, status i kolejny krok.",
    },
    {
      title: "Reagujesz w godziny, nie dni.",
      body: "Ciepły klient zostaje ciepły.",
    },
    {
      title: "Wieczory bez „co ja miałem zrobić”.",
      body: "Agent pamięta za Ciebie.",
    },
  ];
  return (
    <section
      id="rezultat"
      style={{
        padding: compact ? "76px 24px" : "120px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <div style={{ maxWidth: 1080, margin: "0 auto" }}>
        <SectionEyebrow center>REZULTAT</SectionEyebrow>
        <SectionTitle center>Po 30 dniach z&nbsp;Agentem OZE.</SectionTitle>

        <div
          style={{
            marginTop: compact ? 48 : 72,
            display: "grid",
            gridTemplateColumns: compact ? "1fr" : "1fr 1px 1fr",
            gap: compact ? 32 : 48,
            alignItems: "stretch",
          }}
        >
          <ComparisonColumn
            heading="BEZ AGENTA"
            headingColor="rgba(255,255,255,0.5)"
            items={before}
            iconColor="#EF4444"
            iconChar="✗"
            align={compact ? "center" : "right"}
          />
          {compact ? (
            <div
              style={{
                height: 1,
                background: G,
                boxShadow: `0 0 12px ${G}cc`,
                margin: "8px auto",
                width: "60%",
              }}
            />
          ) : (
            <div
              style={{
                width: 1,
                background: G,
                boxShadow: `0 0 12px ${G}cc`,
              }}
            />
          )}
          <ComparisonColumn
            heading="Z AGENTEM OZE"
            headingColor={G}
            items={after}
            iconColor={G}
            iconChar="✓"
            align={compact ? "center" : "left"}
          />
        </div>

        <div
          style={{
            marginTop: compact ? 56 : 88,
            display: "flex",
            flexDirection: "column",
            gap: 24,
            maxWidth: 720,
            marginInline: "auto",
          }}
        >
          {wins.map((w) => (
            <div
              key={w.title}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 16,
                padding: "20px 24px",
                borderRadius: 14,
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <div
                aria-hidden="true"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 16,
                  background: `${G}22`,
                  border: `1px solid ${G}55`,
                  color: G,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 16,
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div>
                <div
                  style={{
                    fontSize: 17,
                    fontWeight: 600,
                    color: "#fff",
                    marginBottom: 6,
                  }}
                >
                  {w.title}
                </div>
                <div style={{ fontSize: 14.5, color: "rgba(255,255,255,0.6)", lineHeight: 1.55 }}>
                  {w.body}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ComparisonColumn({
  heading,
  headingColor,
  items,
  iconColor,
  iconChar,
  align,
}: {
  heading: string;
  headingColor: string;
  items: string[];
  iconColor: string;
  iconChar: string;
  align: "left" | "right" | "center";
}) {
  return (
    <div
      style={{
        textAlign: align,
        display: "flex",
        flexDirection: "column",
        gap: 16,
        alignItems: align === "center" ? "center" : align === "left" ? "flex-start" : "flex-end",
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 1.6,
          textTransform: "uppercase",
          color: headingColor,
        }}
      >
        — {heading}
      </div>
      {items.map((it) => (
        <div
          key={it}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontSize: 15.5,
            color: "rgba(255,255,255,0.85)",
            flexDirection: align === "right" ? "row-reverse" : "row",
          }}
        >
          <span
            aria-hidden="true"
            style={{
              width: 22,
              height: 22,
              borderRadius: 11,
              border: `1px solid ${iconColor}66`,
              background: `${iconColor}1A`,
              color: iconColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 13,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            {iconChar}
          </span>
          <span>{it}</span>
        </div>
      ))}
    </div>
  );
}

// ── TWOJE NARZĘDZIA ───────────────────────────────────────────────────────
function TwojeNarzedziaSection() {
  const compact = useMediaQuery("(max-width: 760px)");
  const tools: { mark: React.ReactNode; name: string }[] = [
    { mark: <SheetsMark />, name: "Google Sheets" },
    { mark: <CalendarMark />, name: "Google Calendar" },
    { mark: <DriveMark />, name: "Google Drive" },
  ];
  return (
    <section
      id="twoje-narzedzia"
      style={{
        padding: compact ? "76px 24px" : "120px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <div style={{ maxWidth: 1000, margin: "0 auto", textAlign: "center" }}>
        <SectionEyebrow center>TWOJE NARZĘDZIA</SectionEyebrow>
        <SectionTitle center>
          Twoja baza klientów żyje
          <br />
          na <span style={{ color: G }}>Twoim koncie Google</span>. Nie w&nbsp;naszym.
        </SectionTitle>
        <div
          style={{
            marginTop: 28,
            color: "rgba(255,255,255,0.65)",
            fontSize: "clamp(15px, 1.4vw, 17px)",
            lineHeight: 1.7,
            maxWidth: 720,
            marginInline: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <p style={{ margin: 0 }}>
            Arkusz, kalendarz i&nbsp;folder ze zdjęciami zakładamy w&nbsp;Twoim Google —
            Sheets, Calendar, Drive. Otwierasz je bezpośrednio, kiedy chcesz.
          </p>
          <p style={{ margin: 0 }}>
            Jeśli kiedyś zrezygnujesz z&nbsp;Agenta OZE, baza klientów zostaje tam,
            gdzie jest: u&nbsp;Ciebie. Nie zabieramy jej ze sobą.
          </p>
        </div>

        <div
          style={{
            marginTop: 48,
            display: "flex",
            flexWrap: "wrap",
            gap: 16,
            justifyContent: "center",
          }}
        >
          {tools.map((t) => (
            <div
              key={t.name}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 12,
                padding: "14px 22px",
                borderRadius: 14,
                background: "rgba(255,255,255,0.025)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <div style={{ width: 28, height: 28, display: "flex" }}>{t.mark}</div>
              <span style={{ fontSize: 15, fontWeight: 500, color: "#fff" }}>{t.name}</span>
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
      q: "Czy moje dane klientów są bezpieczne?",
      a: "Twój arkusz, kalendarz i folder są w Twoim koncie Google. Logowanie przez Google OAuth — nie znamy Twojego hasła. Komunikacja z Telegrama szyfrowana.",
    },
    {
      q: "Czy muszę umieć obsługiwać AI albo programować?",
      a: "Nie. Wysyłasz wiadomość do bota na Telegramie tak jak do kumpla. Agent rozumie polski z odmianami („u Krzywińskim” → Krzywiński). Jak czegoś nie wie — pyta.",
    },
    {
      q: "Co jeśli agent źle zapisze imię albo adres?",
      a: "Każdy zapis czeka na Twoje potwierdzenie. Klikasz „Zapisać” albo „Dopisać” i poprawiasz. Nic nie wpada do arkusza bez Twojej zgody.",
    },
    {
      q: "Co jeśli zrezygnuję?",
      a: "Agent przestaje działać, ale Twój arkusz, kalendarz i folder ze zdjęciami zostają w Twoim Google. Nie zabieramy bazy klientów ze sobą.",
    },
    {
      q: "Czy mogę używać agenta na telefonie?",
      a: "Tak. Cały agent działa w Telegramie — masz go w kieszeni. Dashboard otwierasz w przeglądarce, kiedy chcesz zobaczyć lejek.",
    },
    {
      q: "Faktura VAT?",
      a: "Tak, na firmę. Płatność BLIK, karta lub przelew.",
    },
  ];
  const [open, setOpen] = useState<number>(0);
  return (
    <section
      id="faq"
      style={{ padding: "100px 32px", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        <SectionEyebrow center>FAQ</SectionEyebrow>
        <SectionTitle center>Pytania, które już sobie zadałeś.</SectionTitle>
        <div style={{ marginTop: 48, display: "flex", flexDirection: "column", gap: 6 }}>
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
                  fontSize: 15.5,
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
                    fontSize: 14.5,
                    color: "rgba(255,255,255,0.7)",
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
  const compact = useMediaQuery("(max-width: 760px)");
  return (
    <section
      id="cta-koncowe"
      style={{
        padding: compact ? "100px 24px" : "140px 32px",
        position: "relative",
        overflow: "hidden",
        background: `radial-gradient(ellipse at center bottom, ${G}14 0%, rgba(0,0,0,1) 60%)`,
      }}
    >
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: "32%",
          height: 1,
          background: `linear-gradient(90deg, transparent 0%, ${G}66 50%, transparent 100%)`,
          boxShadow: `0 0 24px ${G}66`,
          pointerEvents: "none",
        }}
      />
      <div style={{ maxWidth: 880, margin: "0 auto", textAlign: "center", position: "relative" }}>
        <h2
          style={{
            fontSize: compact ? "clamp(34px, 9vw, 44px)" : "clamp(40px, 5vw, 68px)",
            lineHeight: 1.05,
            fontWeight: 600,
            margin: "0 0 24px",
            textWrap: "balance" as React.CSSProperties["textWrap"],
          }}
        >
          Każdy dzień bez <span style={{ color: G, textShadow: `0 0 40px ${G}55` }}>Agenta OZE</span>
          <br />
          to leady, których właśnie zapominasz.
        </h2>
        <p
          style={{
            fontSize: "clamp(15px, 1.5vw, 18px)",
            color: "rgba(255,255,255,0.65)",
            maxWidth: 580,
            margin: "0 auto 36px",
            lineHeight: 1.6,
          }}
        >
          3 minuty setup. Pierwszy klient wpada do arkusza jeszcze przed kolejnym
          spotkaniem.
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
          Załóż konto <span aria-hidden="true">→</span>
        </Link>
        <div
          style={{
            marginTop: 18,
            fontSize: 12.5,
            color: "rgba(255,255,255,0.45)",
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
  const compact = useMediaQuery("(max-width: 860px)");
  // TODO: kontakt@oze-agent.pl is a placeholder — swap to live address before launch
  return (
    <footer
      id="kontakt"
      style={{
        borderTop: `1px solid ${G}26`,
        padding: compact ? "48px 24px 24px" : "64px 32px 32px",
        background: "#000",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: compact ? "1fr" : "1.4fr 1fr 1fr",
          gap: compact ? 36 : 48,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <RingLogo />
            <span style={{ fontSize: 17, fontWeight: 600 }}>OZE Agent</span>
          </div>
          <p
            style={{
              fontSize: 13.5,
              color: "rgba(255,255,255,0.55)",
              lineHeight: 1.6,
              margin: 0,
              maxWidth: 360,
            }}
          >
            Asystent sprzedaży dla handlowców OZE. Pilnuje leadów, follow-upów,
            zdjęć i&nbsp;ofert w&nbsp;Telegramie. Żeby żaden ciepły klient nie zniknął.
          </p>
        </div>

        <FooterColumn
          heading="Produkt"
          links={[
            { label: "Jak działa", href: "#dzien-handlowca" },
            { label: "Funkcje", href: "#funkcje" },
            { label: "FAQ", href: "#faq" },
            { label: "Dla firm OZE", href: "/firma" },
          ]}
        />

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <FooterColumn
            heading="Kontakt"
            links={[
              { label: "Email: kontakt@oze-agent.pl", href: "mailto:kontakt@oze-agent.pl" },
              { label: "Telegram: @OZEAgentBot", href: "https://t.me/OZEAgentBot" },
            ]}
          />
          <FooterColumn
            heading="Prawne"
            links={[
              { label: "Polityka prywatności", href: "/polityka-prywatnosci" },
              { label: "Regulamin", href: "/regulamin" },
            ]}
          />
        </div>
      </div>

      <div
        style={{
          maxWidth: 1280,
          margin: "32px auto 0",
          paddingTop: 20,
          borderTop: "1px solid rgba(255,255,255,0.06)",
          textAlign: "center",
          fontSize: 12,
          color: "rgba(255,255,255,0.4)",
        }}
      >
        © 2026 OZE Agent. Wszystkie prawa zastrzeżone.
      </div>
    </footer>
  );
}

function FooterColumn({
  heading,
  links,
}: {
  heading: string;
  links: { label: string; href: string }[];
}) {
  return (
    <div>
      <div
        style={{
          fontSize: 12.5,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: 1.2,
          color: "#fff",
          marginBottom: 14,
        }}
      >
        {heading}
      </div>
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {links.map((l) => {
          const external = l.href.startsWith("http") || l.href.startsWith("mailto:");
          const isAnchor = l.href.startsWith("#");
          const linkStyle: React.CSSProperties = {
            fontSize: 13.5,
            color: "rgba(255,255,255,0.6)",
            textDecoration: "none",
            transition: "color .15s",
          };
          const onEnter = (e: React.MouseEvent<HTMLAnchorElement>) =>
            (e.currentTarget.style.color = G);
          const onLeave = (e: React.MouseEvent<HTMLAnchorElement>) =>
            (e.currentTarget.style.color = "rgba(255,255,255,0.6)");
          return (
            <li key={l.label}>
              {external || isAnchor ? (
                <a
                  href={l.href}
                  {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                  style={linkStyle}
                  onMouseEnter={onEnter}
                  onMouseLeave={onLeave}
                >
                  {l.label}
                </a>
              ) : (
                <Link
                  href={l.href}
                  style={linkStyle}
                  onMouseEnter={onEnter}
                  onMouseLeave={onLeave}
                >
                  {l.label}
                </Link>
              )}
            </li>
          );
        })}
      </ul>
    </div>
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
        letterSpacing: 1.4,
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
        fontSize: "clamp(30px, 4.4vw, 54px)",
        lineHeight: 1.08,
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
