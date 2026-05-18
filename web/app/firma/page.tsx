import Link from "next/link";
import { BrandLink } from "@/components/brand";
import { FirmaContactForm } from "@/components/firma-contact-form";

const G = "#3DFF7A";

export const metadata = {
  title: "Agent OZE dla firm | Agent OZE",
  description:
    "Agent OZE skrojony pod Twoją firmę. Prosty formularz kontaktowy dla właścicieli firm OZE.",
};

export default function FirmaPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#000",
        color: "#fff",
        position: "relative",
        overflowX: "clip",
      }}
    >
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 20% 20%, rgba(61,255,122,0.07), transparent 28%), radial-gradient(circle at 80% 30%, rgba(61,255,122,0.04), transparent 30%), linear-gradient(180deg, #071009 0%, #000 68%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "relative",
          zIndex: 1,
          width: "min(1160px, calc(100% - 40px))",
          minHeight: "100vh",
          margin: "0 auto",
          padding: "28px 0 44px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 18,
          }}
        >
          <BrandLink href="/" style={{ fontWeight: 700 }} />
          <Link
            href="/"
            style={{
              color: "rgba(255,255,255,0.7)",
              textDecoration: "none",
              fontSize: 14,
              fontWeight: 600,
            }}
          >
            strona główna
          </Link>
        </header>

        <section
          className="firma-grid"
          style={{
            flex: 1,
            display: "grid",
            alignItems: "center",
            gap: 48,
            padding: "72px 0 36px",
          }}
        >
          <div>
            <div
              style={{
                color: G,
                textTransform: "uppercase",
                letterSpacing: 2,
                fontSize: 12,
                fontWeight: 800,
                marginBottom: 22,
              }}
            >
              — Dla właścicieli firm OZE
            </div>
            <h1
              style={{
                fontSize: "clamp(40px, 6vw, 78px)",
                lineHeight: 0.96,
                letterSpacing: "-0.04em",
                fontWeight: 700,
                margin: 0,
                maxWidth: 760,
                textWrap: "balance" as React.CSSProperties["textWrap"],
              }}
            >
              Agent OZE skrojony pod Twoją firmę
            </h1>
            <div
              style={{
                marginTop: 30,
                display: "grid",
                gap: 14,
                maxWidth: 680,
              }}
            >
              {[
                "nie tracisz pieniędzy",
                "wspólnie z Twoimi ludźmi zarabiacie więcej",
                "macie mniej na głowie",
              ].map((text) => (
                <div
                  key={text}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    color: "rgba(255,255,255,0.82)",
                    fontSize: "clamp(18px, 2vw, 24px)",
                    lineHeight: 1.35,
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      background: G,
                      boxShadow: "none",
                      flex: "0 0 auto",
                    }}
                  />
                  {text}
                </div>
              ))}
            </div>
          </div>

          <FirmaContactForm />
        </section>
      </div>
      <style>{`
        .firma-grid {
          grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
        }

        @media (max-width: 860px) {
          .firma-grid {
            grid-template-columns: 1fr;
            padding-top: 56px !important;
          }
        }
      `}</style>
    </main>
  );
}
