const faqSections = [
  {
    title: "Dane i Google",
    intro: "Gdzie są informacje o klientach i jak najlepiej przygotować konto.",
    questions: [
      {
        question: "Gdzie są dane klientów?",
        answer:
          "Dane są na Twoim koncie Google: klienci w Arkuszach Google, spotkania i telefony w Kalendarzu Google, zdjęcia na Dysku Google. Polecamy osobne konto Google do pracy z Agent-OZE; dla firmy najlepszym rozwiązaniem jest Google Workspace, bo łatwiej zarządzać dostępem, własnością danych i miejscem na Drive.",
      },
      {
        question: "Czy muszę zakładać nowe konto Google?",
        answer:
          "Nie. Agent może działać na obecnym koncie Google. W praktyce polecamy osobne konto do pracy z klientami, żeby nie mieszać danych sprzedażowych z prywatnymi plikami. Jeśli firma ma zespół handlowców, warto rozważyć Google Workspace, ale nie jest wymagane.",
      },
      {
        question: "Czy mogę edytować dane ręcznie w Google?",
        answer:
          "Tak. Arkusz, kalendarz i folder Drive należą do Ciebie. Możesz je otworzyć ręcznie i poprawić dane, gdy trzeba. Agent i panel web korzystają z tych samych danych.",
      },
      {
        question: "Co się dzieje z danymi, gdy rezygnuję?",
        answer:
          "Agent przestaje działać, ale dane zostają na Twoim koncie Google. Nie zabieramy arkusza, kalendarza ani zdjęć klientów.",
      },
    ],
  },
  {
    title: "Praca z agentem",
    intro: "Jak używać Telegrama i co dzieje się przed zapisem danych.",
    questions: [
      {
        question: "Po co Telegram, skoro jest panel web?",
        answer:
          "Telegram jest do szybkiej pracy w terenie: głosówki, notatki po spotkaniu, nowy klient, status, telefon, zdjęcia. Panel web jest do przeglądania dnia, klientów, kalendarza, płatności i ofert przy biurku.",
      },
      {
        question: "Czy agent zapisuje coś od razu?",
        answer:
          "Nie. Przy dodaniu klienta, notatki, statusu, spotkania, zdjęcia albo wysyłki oferty agent najpierw pokazuje kartę. Dane trafiają dalej dopiero po Twoim potwierdzeniu.",
      },
      {
        question: "Jak pisać do agenta, żeby dobrze zrozumiał?",
        answer:
          "Najlepiej podawać imię, nazwisko i miasto klienta oraz konkretną akcję. Przy sprawach na przyszłość dodaj dzień i godzinę. Jedna wiadomość powinna dotyczyć jednej głównej sprawy.",
      },
      {
        question: "Co jeśli agent pomyli dane albo nie wie, o kogo chodzi?",
        answer:
          "Nie zapisuj karty, jeśli coś jest źle. Dopisz brakujące informacje albo anuluj. Gdy jest kilku podobnych klientów, agent powinien poprosić o doprecyzowanie.",
      },
    ],
  },
  {
    title: "Panel, oferty i konto",
    intro: "Co sprawdzisz w panelu i gdzie kończy się rola webappu.",
    questions: [
      {
        question: "Do czego służy panel web?",
        answer:
          "Panel pokazuje bazę klientów, plan dnia, kalendarz, klientów wymagających decyzji, płatności i oferty. To miejsce kontroli, nie czat z agentem.",
      },
      {
        question: "Czy webapp edytuje CRM?",
        answer:
          "Zwykłe zmiany klientów robisz przez Telegram albo bezpośrednio w Google. Panel pokazuje dane i prowadzi do właściwych miejsc, żeby nie tworzyć drugiej bazy obok Google.",
      },
      {
        question: "Jak działają oferty?",
        answer:
          "W panelu tworzysz szablony ofert i testujesz PDF. Prawdziwa wysyłka do klienta idzie przez Telegram i Gmail dopiero po potwierdzeniu.",
      },
      {
        question: "Gdzie sprawdzę płatność i fakturę?",
        answer:
          "Status subskrypcji zobaczysz w zakładce Płatności. Tam powinny być też informacje potrzebne do rozliczenia i faktury.",
      },
    ],
  },
] as const;

export default function FaqPage() {
  const totalQuestions = faqSections.reduce(
    (count, section) => count + section.questions.length,
    0,
  );
  const quickTopics = ["Google", "Telegram", "Panel", "Oferty", "Płatności"] as const;

  return (
    <div className="mx-auto max-w-7xl pb-14">
      <header className="border-b border-white/10 pb-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#3DFF7A]">
              FAQ
            </p>
            <h1 className="mt-3 text-4xl font-semibold leading-tight text-white">
              Najczęstsze pytania
            </h1>
            <p className="mt-4 text-base leading-7 text-zinc-400">
              Krótkie odpowiedzi na rzeczy, które najczęściej pojawiają się po
              uruchomieniu konta: dane, Google, Telegram, panel, oferty i płatności.
            </p>
          </div>

          <div className="max-w-sm lg:justify-self-end">
            <div className="rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 px-4 py-3 shadow-[0_0_30px_rgba(61,255,122,0.06)]">
              <p className="text-2xl font-semibold leading-none text-white">
                {totalQuestions}
              </p>
              <p className="mt-1 text-xs font-medium uppercase tracking-[0.16em] text-[#3DFF7A]">
                odpowiedzi
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {quickTopics.map((topic) => (
            <span
              key={topic}
              className="rounded-[8px] border border-white/10 bg-white/[0.035] px-3 py-2 text-xs font-medium text-zinc-300"
            >
              {topic}
            </span>
          ))}
        </div>
      </header>

      <div className="mt-9 space-y-11">
        {faqSections.map((section, sectionIndex) => (
          <section
            key={section.title}
            className="grid gap-5 border-t border-white/10 pt-8 first:border-t-0 first:pt-0 lg:grid-cols-[0.72fr_1.28fr]"
          >
            <div className="lg:sticky lg:top-24 lg:self-start">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 text-sm font-semibold text-[#3DFF7A]">
                  {String(sectionIndex + 1).padStart(2, "0")}
                </span>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-white">
                  {section.title}
                </p>
              </div>
              <p className="mt-3 max-w-sm text-sm leading-6 text-zinc-400">
                {section.intro}
              </p>
            </div>

            <div className="grid gap-3">
              {section.questions.map((item, questionIndex) => (
                <article
                  key={item.question}
                  className="relative overflow-hidden rounded-[8px] border border-white/10 bg-white/[0.035] p-5 shadow-[0_0_30px_rgba(61,255,122,0.06)]"
                >
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-[#3DFF7A]/45 via-[#3DFF7A]/10 to-transparent" />
                  <div className="flex items-start gap-4">
                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] border border-white/10 bg-black/30 text-xs font-semibold text-[#3DFF7A]">
                      {String(questionIndex + 1).padStart(2, "0")}
                    </span>
                    <div className="min-w-0">
                      <h2 className="text-base font-semibold leading-6 text-white">
                        {item.question}
                      </h2>
                      <p className="mt-3 text-sm leading-6 text-zinc-400">
                        {item.answer}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
