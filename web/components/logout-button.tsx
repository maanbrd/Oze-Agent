import { logout } from "@/app/auth/actions";

export function LogoutButton({ className = "" }: { className?: string }) {
  return (
    <form action={logout}>
      <button
        type="submit"
        className={`rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white ${className}`}
      >
        Wyloguj
      </button>
    </form>
  );
}
