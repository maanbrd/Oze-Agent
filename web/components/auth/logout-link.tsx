import Link from "next/link";

export function LogoutLink() {
  return (
    <Link
      href="/logout"
      className="rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
    >
      Wyloguj
    </Link>
  );
}
