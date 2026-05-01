import { CrmNotice } from "@/components/crm-notice";

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Import</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Import klientów z pliku
        </h1>
      </div>

      <CrmNotice />

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <p className="text-sm leading-7 text-zinc-300">
          Import CSV/Excel będzie osobnym, kontrolowanym przepływem. Ten ekran
          nie zapisuje nic do CRM i nie ma formularza uploadu, dopóki nie będzie
          gotowego mapowania kolumn oraz kontroli duplikatów.
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {["Upload pliku", "Mapowanie kolumn", "Podgląd duplikatów"].map((item) => (
            <div key={item} className="rounded-[8px] border border-white/10 bg-black/20 p-4 text-sm text-zinc-400">
              {item}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
