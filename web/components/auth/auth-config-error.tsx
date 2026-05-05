import Link from "next/link";

export function AuthConfigError({ detail }: { detail: string | null }) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_24%_12%,rgba(61,255,122,0.2),transparent_34%),radial-gradient(circle_at_78%_22%,rgba(20,184,166,0.14),transparent_32%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
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

        <section className="flex flex-1 items-center py-16">
          <div className="max-w-2xl rounded-[8px] border border-[#3DFF7A]/20 bg-white/[0.04] p-6 shadow-2xl shadow-black/30">
            <p className="mb-4 text-xs font-semibold uppercase text-[#3DFF7A]">
              Konfiguracja
            </p>
            <h1 className="text-4xl font-semibold leading-tight text-white">
              Logowanie wymaga konfiguracji Supabase.
            </h1>
            <p className="mt-5 text-base leading-7 text-zinc-300">
              {detail ??
                "Brak wymaganych zmiennych środowiskowych dla web appu."}
            </p>
            <div className="mt-6 rounded-[8px] border border-white/10 bg-black/30 p-4 text-sm leading-7 text-zinc-300">
              Uzupełnij lokalny plik{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                web/.env.local
              </code>{" "}
              o{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                NEXT_PUBLIC_SUPABASE_URL
              </code>{" "}
              albo{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                SUPABASE_URL
              </code>{" "}
              oraz{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
              </code>{" "}
              albo{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                NEXT_PUBLIC_SUPABASE_ANON_KEY
              </code>{" "}
              albo{" "}
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-100">
                SUPABASE_KEY
              </code>
              , a potem zrestartuj dev server.
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
