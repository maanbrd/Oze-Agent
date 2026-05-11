import Link from "next/link";

type AppShellProps = {
  active: "dashboard" | "oferty";
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <main className="oze-app relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_22%_8%,rgba(61,255,122,0.16),transparent_32%),radial-gradient(circle_at_82%_18%,rgba(20,184,166,0.12),transparent_30%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3DFF7A]/60 to-transparent" />
      <Link href="/" className="absolute left-5 top-5 z-20 flex items-center gap-3 text-sm font-semibold tracking-[0] text-white">
        <span className="grid h-8 w-8 place-items-center rounded-full border border-[#3DFF7A]/40 bg-[#3DFF7A]/10 shadow-[0_0_24px_rgba(61,255,122,0.18)]">
          <span className="h-2.5 w-2.5 rounded-full bg-[#3DFF7A]" />
        </span>
        OZE Agent
      </Link>
      <section className="relative min-w-0">{children}</section>
    </main>
  );
}
