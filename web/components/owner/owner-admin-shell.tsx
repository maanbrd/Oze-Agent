"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLink } from "@/components/brand";
import { LogoutLink } from "@/components/auth/logout-link";
import type { CurrentAccount } from "@/lib/api/account";

const ownerNavItems = [
  ["Centrum Właściciela", "/admin"],
  ["Analityka danych OZE", "/admin/analityka-danych-oze"],
  ["Operacje i zdrowie", "/admin/operacje-zdrowie"],
  ["Klienci i konta", "/admin/klienci-konta"],
  ["Płatności i subskrypcje", "/admin/platnosci-subskrypcje"],
  ["Produkty i oferty", "/admin/produkty-oferty"],
  ["Integracje", "/admin/integracje"],
  ["Raporty", "/admin/raporty"],
  ["Ustawienia", "/admin/ustawienia"],
] as const;

export function OwnerAdminShell({
  account,
  children,
}: {
  account: CurrentAccount;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const email = account.profile?.email ?? account.email ?? "Konto admina";
  const initials = (account.profile?.name ?? email)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="grid min-h-screen lg:grid-cols-[248px_1fr]">
        <aside className="border-b border-white/10 bg-[#080a0d] px-5 py-5 lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
          <BrandLink href="/admin" className="text-sm font-semibold text-white" />

          <nav className="mt-7 grid gap-1">
            {ownerNavItems.map(([label, href], index) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={
                    active
                      ? "flex items-center gap-2 rounded-[8px] border border-[#3DFF7A]/15 bg-[#3DFF7A]/12 px-3 py-2 text-sm font-semibold text-[#3DFF7A]"
                      : "flex items-center gap-2 rounded-[8px] px-3 py-2 text-sm font-medium text-zinc-400 transition hover:bg-white/[0.05] hover:text-white"
                  }
                >
                  <span className={active ? "text-[10px] text-[#3DFF7A]" : "text-[10px] text-zinc-600"}>
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-7 rounded-[8px] border border-white/10 bg-white/[0.04] p-3 text-xs leading-5 text-zinc-400">
            Warstwa właściciela. CRM użytkownika działa osobno i nie jest renderowany
            na koncie admina.
          </div>
        </aside>

        <section className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-[#050607]/92 px-5 py-4 backdrop-blur lg:px-8">
            <div className="grid gap-3 md:grid-cols-[minmax(260px,560px)_1fr_auto] md:items-center">
              <label className="relative text-xs font-medium uppercase text-zinc-500">
                <span className="sr-only">Szukaj</span>
                <input
                  type="search"
                  placeholder="Szukaj klientów, ofert, miast, komponentów..."
                  className="h-10 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 text-sm normal-case text-white outline-none placeholder:text-zinc-600 focus:border-[#3DFF7A]/70"
                />
                <span className="absolute right-3 top-3 text-xs text-zinc-600">⌘ K</span>
              </label>
              <div />
              <div className="flex min-w-0 items-center justify-end gap-3">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white/10 text-xs font-semibold text-white">
                  {initials || "A"}
                </span>
                <div className="hidden min-w-0 md:block">
                  <p className="truncate text-sm font-semibold text-white">{email}</p>
                  <p className="text-xs text-zinc-500">Właściciel</p>
                </div>
                <LogoutLink />
              </div>
            </div>
          </header>
          <div className="px-5 py-5 lg:px-8">{children}</div>
        </section>
      </div>
    </main>
  );
}
