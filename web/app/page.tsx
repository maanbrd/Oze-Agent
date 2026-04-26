export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-6">
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
        Agent-OZE — centrum dowodzenia handlowca
      </h1>
      <p className="max-w-prose text-center text-base text-[color:var(--muted)] sm:text-lg">
        Narzędzie do pracy przy biurku dla handlowca OZE. Rozmowa z agentem dzieje się w Telegramie. Tutaj
        przeglądasz lejek, plan dnia i klientów wymagających działania.
      </p>
      <p className="text-sm text-[color:var(--muted)]">Phase 0A — scaffold</p>
    </main>
  );
}
