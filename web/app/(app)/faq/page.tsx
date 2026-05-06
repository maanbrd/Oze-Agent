export default function FaqPage() {
  const questions = [
    ["Gdzie są dane klientów?", "W Twoim Google: klienty w Sheets, spotkania w Calendar, zdjęcia w Drive."],
    ["Czy web app edytuje CRM?", "Nie. Panel pokazuje dane read-only i prowadzi do bezpośrednich linków Google."],
    ["Po co Telegram?", "Telegram jest do szybkich wpisów w terenie. Panel jest do przeglądania przy biurku."],
    ["Jak działa płatność?", "Stripe Checkout uruchamia subskrypcję, a webhook aktualizuje status konta."],
  ];

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">FAQ</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Najczęstsze pytania</h1>
      </div>

      <section className="grid gap-3">
        {questions.map(([question, answer]) => (
          <article key={question} className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <h2 className="text-sm font-semibold text-white">{question}</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">{answer}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
