export default function InstructionPage() {
  const sections = [
    ["Dodawanie klienta", "Mówisz albo piszesz w Telegramie. Bot pokazuje kartę, zapis jest dopiero po potwierdzeniu."],
    ["Panel web", "Tutaj czytasz dane z Sheets i Calendar, filtrujesz, sprawdzasz plan dnia i otwierasz linki Google."],
    ["Edycja CRM", "Klienty zmieniasz w Sheets. Spotkania i akcje zmieniasz w Calendar. Web app nie zapisuje CRM."],
    ["Płatności", "Subskrypcję obsługuje Stripe. Status widzisz w sekcji Płatności."],
  ];

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Instrukcja</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Jak pracować z Agent-OZE
        </h1>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        {sections.map(([title, body]) => (
          <article key={title} className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <h2 className="text-sm font-semibold text-white">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">{body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
