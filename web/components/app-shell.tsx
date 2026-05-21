import { BrandLink } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import { OnboardingGate } from "@/components/onboarding-gate";
import type { OnboardingStatus } from "@/lib/api/onboarding";

type AppShellProps = {
  active: "dashboard" | "oferty";
  children: React.ReactNode;
  onboardingStatus?: OnboardingStatus | null;
};

export function AppShell({ children, onboardingStatus = null }: AppShellProps) {
  return (
    <main className="oze-app relative min-h-screen overflow-x-clip bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_22%_8%,rgba(61,255,122,0.16),transparent_32%),radial-gradient(circle_at_82%_18%,rgba(20,184,166,0.12),transparent_30%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3DFF7A]/60 to-transparent" />
      <BrandLink
        href="/"
        className="absolute left-5 top-5 z-20 text-sm font-semibold tracking-[0] text-white"
      />
      <div className="absolute right-5 top-5 z-20">
        <LogoutButton />
      </div>
      <section className="relative min-w-0">
        <OnboardingGate status={onboardingStatus} />
        {children}
      </section>
    </main>
  );
}
