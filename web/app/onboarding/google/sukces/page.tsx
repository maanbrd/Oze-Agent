import Link from "next/link";

export default function GoogleSuccessPage() {
  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-2xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Google</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">
          Google jest połączony.
        </h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Teraz utworzymy lub podłączymy zasoby: Sheets, Calendar i Drive.
        </p>
        <Link
          href="/onboarding/zasoby"
          className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
        >
          Dalej
        </Link>
      </section>
    </main>
  );
}
