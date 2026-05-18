const foundations = [
  {
    title: "Telegram",
    body: "Piszesz albo mówisz tak, jak w terenie. Agent układa z tego kartę klienta, spotkanie, notatkę, zmianę statusu albo wysyłkę oferty.",
  },
  {
    title: "Panel web",
    body: "Przeglądasz bazę, dzień pracy, klientów wymagających decyzji, płatności i szablony ofert. Panel prowadzi też do Twojego Google.",
  },
  {
    title: "Google",
    body: "Arkusz Google trzyma klientów. Kalendarz Google trzyma spotkania i akcje. Dysk Google trzyma zdjęcia. Agent pracuje na tych danych po Twoim potwierdzeniu.",
  },
] as const;

const confirmationSteps = [
  "Piszesz wiadomość albo nagrywasz głos.",
  "Agent pokazuje kartę z tym, co zrozumiał.",
  "Sprawdzasz dane i wybierasz jedną z akcji.",
  "Dopiero po zielonym przycisku dane trafiają do Google.",
] as const;

const buttonRules = [
  ["✅ Zapisać", "zapisuje klienta, notatkę, status, spotkanie albo zdjęcie"],
  ["➕ Dopisać", "pozwala dopisać brakujące dane przed zapisem"],
  ["❌ Anulować", "zamyka sprawę bez zapisu"],
] as const;

const agentExamples = [
  {
    title: "Dodanie klienta",
    example:
      "Dodaj klienta Jan Kowalski z Warszawy, tel. 600 100 200, PV 8 kW, dach południe, chce wycenę.",
    reacts:
      "Agent pokaże kartę klienta. Dane kontaktowe trafią do pól klienta, a szczegóły techniczne i komentarze do notatek.",
    remember:
      "Imię, nazwisko i miasto są najważniejsze. Dzięki temu później agent wie, o którego klienta chodzi.",
  },
  {
    title: "Spotkanie, telefon, mail albo follow-up",
    example: "Jutro o 10 spotkanie z Janem Kowalskim z Warszawy na Piłsudskiego 12.",
    reacts:
      "Agent przygotuje kartę wydarzenia w Kalendarzu Google. Jeżeli klient już jest w bazie, użyje jego danych.",
    remember:
      "Podawaj dzień i godzinę. Gdy mówisz tylko o przyszłej wysyłce maila, agent zapisuje to jako akcję w kalendarzu.",
  },
  {
    title: "Notatka po rozmowie",
    example: "Jan Kowalski z Warszawy: żona chce magazyn, decyzja po weekendzie.",
    reacts:
      "Agent dopisze notatkę po potwierdzeniu. Jeśli napiszesz też oddzwonić w piątek o 10, przygotuje jedną kartę: notatka + telefon w kalendarzu.",
    remember:
      "Gdy przed chwilą była rozmowa o tym samym kliencie, możesz napisać krócej: dopisz, że żona chce magazyn.",
  },
  {
    title: "Zmiana statusu",
    example: "Jan Kowalski z Warszawy dostał ofertę.",
    reacts:
      "Agent rozpozna zmianę statusu i pokaże kartę przed zapisem. Po zapisie może zapytać, co dalej z klientem.",
    remember:
      "Nie musisz znać dokładnej nazwy statusu. Frazy typu podpisał, odpada, oferta wysłana są wystarczające.",
  },
  {
    title: "Plan dnia",
    example: "co mam jutro?",
    reacts:
      "Agent pokaże plan z Kalendarza Google. To jest odczyt, więc nie ma karty potwierdzenia.",
    remember:
      "Możesz pytać o dziś, jutro albo konkretny dzień. Wolne okna nie są jeszcze obsługiwane przez agenta.",
  },
  {
    title: "Oferta dla klienta",
    example: "Wyślij ofertę numer 2 Janowi Kowalskiemu z Warszawy.",
    reacts:
      "Agent znajdzie gotowy szablon z sekcji Oferty, sprawdzi klienta i pokaże kartę wysyłki. Mail wychodzi dopiero po kliknięciu ✅ Wysłać.",
    remember:
      "Szablony ofert tworzysz w panelu web. Prawdziwa wysyłka do klienta dzieje się w Telegramie.",
  },
  {
    title: "Zdjęcia",
    example: "Wyślij zdjęcie z podpisem: Jan Kowalski Warszawa, dach od strony ogrodu.",
    reacts:
      "Agent przypisze zdjęcie do klienta po potwierdzeniu i zapisze je na Dysku Google.",
    remember:
      "Jeśli wysyłasz kilka zdjęć pod rząd, agent trzyma krótką sesję dla tego samego klienta.",
  },
  {
    title: "Głos",
    example: "Nagraj wiadomość tak, jakbyś dyktował notatkę po spotkaniu.",
    reacts:
      "Agent przepisze głos na tekst i pokaże kartę do zatwierdzenia. Po zatwierdzeniu traktuje tekst jak zwykłą wiadomość.",
    remember:
      "Mów imię, nazwisko i miasto klienta. To najbardziej pomaga w poprawnym dopasowaniu.",
  },
] as const;

const writingRules = [
  "Używaj imienia, nazwiska i miasta: Jan Kowalski z Warszawy.",
  "Dodawaj datę i godzinę przy każdej akcji w przyszłości.",
  "Pisz produkt zwyczajnie: PV, pompa ciepła, magazyn energii, PV plus magazyn.",
  "Jedna wiadomość najlepiej dotyczy jednej sprawy: jednego klienta, jednej notatki, jednego spotkania.",
  "Samo nazwisko to za mało. Agent może wtedy poprosić o doprecyzowanie.",
  "Gdy karta jest otwarta, możesz dopisać brakujący telefon, email, adres, produkt albo źródło.",
] as const;

const webSections = [
  ["Dashboard", "Szybki obraz dnia, aktywnych klientów, spotkań, ofert i lejka."],
  ["Wymagają decyzji", "Lista klientów, których trzeba ruszyć dalej albo świadomie zostawić."],
  ["Klienci", "Tabela z bazy klientów z Arkusza Google, filtrowanie i linki do Google."],
  ["Kalendarz", "Spotkania i akcje z Kalendarza Google pogrupowane po dniach."],
  ["Oferty", "Tworzenie szablonów ofert, profil sprzedawcy, logo, treść maila i testowy PDF."],
  ["Płatności", "Status subskrypcji i przejście do płatności, gdy konto tego wymaga."],
] as const;

const doesNotDo = [
  "Nie zapisuje nic od razu po samej wiadomości.",
  "Nie zmienia klientów z poziomu tabeli w panelu web.",
  "Nie obsługuje kilku spotkań naraz w jednej wiadomości.",
  "Nie szuka jeszcze wolnych okien w kalendarzu.",
  "Nie odpowiada w grupach Telegrama.",
  "Nie wysyła oferty bez osobnej karty ✅ Wysłać.",
] as const;

export function InstructionGuide() {
  return (
    <div className="mx-auto max-w-7xl space-y-14 pb-16">
      <header className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#3DFF7A]">
            Instrukcja
          </p>
          <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight text-white md:text-5xl">
            Instrukcja użytkowa Agent OZE
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-zinc-300">
            Agent OZE pomaga handlowcowi OZE prowadzić klientów bez przeklikiwania
            się po arkuszach w trakcie dnia. Najszybciej pracujesz z nim w
            Telegramie, a panel web służy do przeglądania, kontroli i ustawiania
            ofert.
          </p>
        </div>

        <div className="rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 p-5">
          <p className="text-sm font-semibold text-white">
            Najważniejsza zasada: agent nic nie zapisuje od razu
          </p>
          <p className="mt-3 text-sm leading-6 text-zinc-300">
            Najpierw widzisz kartę. Dopiero Twoje kliknięcie zapisuje dane w
            Google. Jeśli coś się nie zgadza, dopisujesz albo anulujesz.
          </p>
          <div className="mt-5 grid gap-2 sm:grid-cols-3">
            {buttonRules.map(([label, body]) => (
              <div
                key={label}
                className="rounded-[8px] border border-white/10 bg-black/25 p-3"
              >
                <p className="text-sm font-semibold text-white">{label}</p>
                <p className="mt-2 text-xs leading-5 text-zinc-400">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        {foundations.map((item) => (
          <GuideCard key={item.title} title={item.title}>
            {item.body}
          </GuideCard>
        ))}
      </section>

      <GuideSection
        number="01"
        eyebrow="Jak wygląda praca"
        title="Od wiadomości do zapisu"
        intro="Agent jest szybki, ale nie działa po cichu. Każda zmiana przechodzi przez prosty podgląd."
      >
        <div className="grid gap-3 md:grid-cols-4">
          {confirmationSteps.map((step, index) => (
            <div
              key={step}
              className="rounded-[8px] border border-white/10 bg-white/[0.04] p-4"
            >
              <span className="text-xs font-semibold text-[#3DFF7A]">
                Krok {index + 1}
              </span>
              <p className="mt-3 text-sm leading-6 text-zinc-300">{step}</p>
            </div>
          ))}
        </div>
      </GuideSection>

      <GuideSection
        number="02"
        eyebrow="Telegram"
        title="Co możesz napisać do agenta"
        intro="Poniższe przykłady pokazują naturalny styl wiadomości. Nie musisz używać komend ani formularzy."
      >
        <div className="space-y-8">
          <div>
            <SubsectionTitle>Podstawowe wpisy</SubsectionTitle>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {agentExamples.slice(0, 4).map((item) => (
                <ExampleCard
                  key={item.title}
                  title={item.title}
                  example={item.example}
                  reacts={item.reacts}
                  remember={item.remember}
                />
              ))}
            </div>
          </div>

          <div>
            <SubsectionTitle>Odczyt, oferty i załączniki</SubsectionTitle>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {agentExamples.slice(4).map((item) => (
                <ExampleCard
                  key={item.title}
                  title={item.title}
                  example={item.example}
                  reacts={item.reacts}
                  remember={item.remember}
                />
              ))}
            </div>
          </div>
        </div>
      </GuideSection>

      <GuideSection
        number="03"
        eyebrow="Sposób pisania"
        title="Jak pisać, żeby agent dobrze zrozumiał"
        intro="Najlepsza wiadomość ma klienta, miejsce i konkretną akcję. Reszta może być opisana zwyczajnym językiem."
      >
        <div className="grid gap-3 md:grid-cols-2">
          {writingRules.map((rule) => (
            <div
              key={rule}
              className="flex gap-3 rounded-[8px] border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-zinc-300"
            >
              <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[#3DFF7A]" />
              <span>{rule}</span>
            </div>
          ))}
        </div>
      </GuideSection>

      <GuideSection
        number="04"
        eyebrow="Panel web"
        title="Co znajdziesz w webappie"
        intro="Panel jest miejscem kontroli. Nie zastępuje Telegrama w szybkiej pracy terenowej i nie służy do ręcznej edycji CRM."
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {webSections.map(([title, body]) => (
            <GuideCard key={title} title={title}>
              {body}
            </GuideCard>
          ))}
        </div>
      </GuideSection>

      <section className="grid gap-5 border-t border-white/10 pt-10 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#3DFF7A]">
            Google
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-white">
            Gdzie są dane
          </h2>
          <div className="mt-5 grid gap-3">
            <DataPlace title="Arkusz Google" body="klienci, statusy, produkty, notatki i następne kroki" />
            <DataPlace title="Kalendarz Google" body="spotkania, telefony, wysyłki ofert i follow-upy" />
            <DataPlace title="Dysk Google" body="zdjęcia przypisane do klientów" />
          </div>
        </div>

        <div className="rounded-[8px] border border-amber-300/20 bg-amber-300/10 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">
            Granice
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-white">
            Czego agent teraz nie robi
          </h2>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {doesNotDo.map((item) => (
              <p
                key={item}
                className="rounded-[8px] border border-amber-200/15 bg-black/20 p-4 text-sm leading-6 text-amber-50/90"
              >
                {item}
              </p>
            ))}
          </div>
        </div>
      </section>

      <GuideSection
        number="05"
        eyebrow="Codzienny rytm"
        title="Jak korzystać w praktyce"
        intro="Najprościej działać według jednego powtarzalnego schematu."
      >
        <div className="grid gap-4 md:grid-cols-3">
          <GuideCard title="Rano">
            Sprawdź plan dnia w Telegramie albo na Dashboardzie. W dni robocze
            agent może wysłać poranny skrót z terminarzem i sprawami do
            dopilnowania.
          </GuideCard>
          <GuideCard title="Po kontakcie z klientem">
            Od razu podyktuj notatkę, nowy status albo kolejną akcję. Nie czekaj
            do wieczora z przepisywaniem.
          </GuideCard>
          <GuideCard title="Przy biurku">
            Wejdź w Klientów, Kalendarz, Oferty i Wymagają decyzji. Tam
            sprawdzasz stan pracy i porządkujesz szablony ofert.
          </GuideCard>
        </div>
      </GuideSection>
    </div>
  );
}

function GuideSection({
  number,
  eyebrow,
  title,
  intro,
  children,
}: {
  number: string;
  eyebrow: string;
  title: string;
  intro: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-6 border-t border-white/10 pt-10">
      <div className="grid gap-4 md:grid-cols-[96px_1fr]">
        <div className="flex items-start gap-3">
          <span className="rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-3 py-2 text-sm font-semibold text-[#3DFF7A]">
            {number}
          </span>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#3DFF7A]">
            {eyebrow}
          </p>
          <h2 className="mt-2 text-3xl font-semibold leading-tight text-white md:text-4xl">
            {title}
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-7 text-zinc-400">
            {intro}
          </p>
        </div>
      </div>
      {children}
    </section>
  );
}

function SubsectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.16em] text-zinc-200">
      <span className="h-px w-10 bg-[#3DFF7A]/60" />
      {children}
    </h3>
  );
}

function GuideCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-zinc-400">{children}</p>
    </article>
  );
}

function ExampleCard({
  title,
  example,
  reacts,
  remember,
}: {
  title: string;
  example: string;
  reacts: string;
  remember: string;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-white/[0.035] p-5">
      <h4 className="text-lg font-semibold text-white">{title}</h4>
      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-[#3DFF7A]">
        Przykład
      </p>
      <p className="mt-2 rounded-[8px] border border-[#3DFF7A]/20 bg-[#3DFF7A]/10 px-4 py-3 text-sm leading-6 text-zinc-100">
        {example}
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
            Co zrobi agent
          </p>
          <p className="mt-2 text-sm leading-6 text-zinc-300">{reacts}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
            Warto wiedzieć
          </p>
          <p className="mt-2 text-sm leading-6 text-zinc-500">{remember}</p>
        </div>
      </div>
    </article>
  );
}

function DataPlace({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-sm font-semibold text-white">{title}</p>
      <p className="mt-2 text-sm leading-6 text-zinc-400">{body}</p>
    </div>
  );
}
