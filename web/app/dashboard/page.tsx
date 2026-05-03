import { AppShell } from "@/components/app-shell";

export default function DashboardPage() {
  return (
    <AppShell active="dashboard">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-6 sm:px-8">
        <header>
          <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
            Panel
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0] text-white">
            Dashboard
          </h1>
        </header>
        <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5 text-sm text-zinc-300">
          Dashboard zostaje poza zakresem generatora ofert.
        </div>
      </div>
    </AppShell>
  );
}
