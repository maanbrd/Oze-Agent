import Link from "next/link";

type PlaceholderPageProps = {
  eyebrow: string;
  title: string;
  body: string;
  highlights?: string[];
  primaryLabel?: string;
  primaryHref?: string;
  secondaryLabel?: string;
  secondaryHref?: string;
  note?: string;
};

export function PlaceholderPage({
  eyebrow,
  title,
  body,
  highlights = [],
  primaryLabel = "Wróć na stronę główną",
  primaryHref = "/",
  secondaryLabel,
  secondaryHref,
  note,
}: PlaceholderPageProps) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_24%_12%,rgba(61,255,122,0.2),transparent_34%),radial-gradient(circle_at_78%_22%,rgba(20,184,166,0.14),transparent_32%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3DFF7A]/60 to-transparent" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-3 text-sm font-semibold text-white"
          >
            <span className="grid h-8 w-8 place-items-center rounded-full border border-[#3DFF7A]/40 bg-[#3DFF7A]/10 shadow-[0_0_24px_rgba(61,255,122,0.18)]">
              <span className="h-2.5 w-2.5 rounded-full bg-[#3DFF7A]" />
            </span>
            OZE Agent
          </Link>
          <Link
            href="/"
            className="rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
          >
            Landing
          </Link>
        </header>

        <section className="flex flex-1 items-center py-16 sm:py-20">
          <div className="max-w-3xl">
            <p className="mb-5 text-xs font-semibold uppercase text-[#3DFF7A]">
              {eyebrow}
            </p>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[0.98] text-white sm:text-6xl lg:text-7xl">
              {title}
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-zinc-300 sm:text-xl">
              {body}
            </p>

            {highlights.length > 0 ? (
              <div className="mt-9 grid gap-3 sm:grid-cols-3">
                {highlights.map((item) => (
                  <div
                    key={item}
                    className="rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm leading-6 text-zinc-300"
                  >
                    <span className="mr-2 inline-block h-2 w-2 rounded-full bg-[#3DFF7A]" />
                    {item}
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <Link
                href={primaryHref}
                className="inline-flex items-center justify-center rounded-full bg-[#3DFF7A] px-6 py-3 text-sm font-semibold text-black shadow-[0_0_36px_rgba(61,255,122,0.22)] transition hover:translate-y-[-1px] hover:bg-[#6DFF98]"
              >
                {primaryLabel}
              </Link>
              {secondaryLabel && secondaryHref ? (
                <Link
                  href={secondaryHref}
                  className="inline-flex items-center justify-center rounded-full border border-white/14 px-6 py-3 text-sm font-semibold text-zinc-200 transition hover:border-[#3DFF7A]/60 hover:text-white"
                >
                  {secondaryLabel}
                </Link>
              ) : null}
            </div>

            {note ? (
              <p className="mt-7 max-w-2xl text-sm leading-6 text-zinc-500">
                {note}
              </p>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
