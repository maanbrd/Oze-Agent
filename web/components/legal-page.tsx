import Link from "next/link";
import { BrandLink } from "@/components/brand";

type LegalSection = {
  title: string;
  body?: string[];
  bullets?: string[];
};

type LegalPageProps = {
  title: string;
  lead: string;
  effectiveDate: string;
  sections: LegalSection[];
};

export function LegalPage({
  title,
  lead,
  effectiveDate,
  sections,
}: LegalPageProps) {
  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="border-b border-white/10 bg-[#0b0d10]">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <BrandLink href="/" className="text-sm font-semibold text-white" />
          <Link
            href="/"
            className="rounded-[8px] border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
          >
            Strona główna
          </Link>
        </div>
      </div>

      <article className="mx-auto w-full max-w-5xl px-5 py-12 sm:px-8 sm:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#3DFF7A]">
          Dokument prawny
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl">
          {title}
        </h1>
        <p className="mt-6 max-w-3xl text-lg leading-8 text-zinc-300">{lead}</p>
        <p className="mt-5 text-sm text-zinc-500">Obowiązuje od: {effectiveDate}</p>

        <div className="mt-12 space-y-10">
          {sections.map((section) => (
            <section key={section.title} className="border-t border-white/10 pt-8">
              <h2 className="text-2xl font-semibold text-white">{section.title}</h2>
              {section.body?.map((paragraph) => (
                <p key={paragraph} className="mt-4 max-w-3xl text-base leading-7 text-zinc-300">
                  {paragraph}
                </p>
              ))}
              {section.bullets ? (
                <ul className="mt-5 max-w-3xl space-y-3 text-base leading-7 text-zinc-300">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="flex gap-3">
                      <span className="mt-[0.68em] h-1.5 w-1.5 shrink-0 rounded-full bg-[#3DFF7A]" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          ))}
        </div>
      </article>
    </main>
  );
}
