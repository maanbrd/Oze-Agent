import type { Metadata } from "next";
import { LegalPage } from "@/components/legal-page";
import { BILLING_EMAIL, SUPPORT_EMAIL } from "@/components/brand";

// TODO: oddzielna umowa B2B dla zespołów sprzedażowych i klientów enterprise.
// Po uruchomieniu przez polski podmiot potrzebna będzie aktualizacja regulaminu
// oraz komunikacja zmiany operatora do użytkowników.

export const metadata: Metadata = {
  title: "Regulamin | Agent OZE",
  description: "Regulamin usługi Agent OZE dla użytkowników panelu i bota.",
};

export default function TermsPage() {
  return (
    <LegalPage
      title="Regulamin"
      lead="Regulamin określa zasady korzystania z Agent OZE: panelu webowego, bota Telegram, integracji Google, generatora ofert i subskrypcji."
      effectiveDate="24.05.2026"
      sections={[
        {
          title: "Operator usługi",
          body: [
            "Operatorem publicznej usługi Agent OZE jest GREAT MF LLC, EIN 36-5120312, 810 Pony Express Rd, Cheyenne, WY 82009, USA. GREAT MF LLC jest tymczasowym operatorem usługi do czasu przeniesienia lub uruchomienia obsługi przez polski podmiot.",
            `Kontakt techniczny i reklamacyjny: ${SUPPORT_EMAIL}. Kontakt w sprawach płatności: ${BILLING_EMAIL}.`,
            "Jeżeli w przyszłości operatorem zostanie polski podmiot, nastąpi aktualizacja regulaminu i komunikacja zmiany użytkownikom zgodnie z zasadami zmiany regulaminu.",
          ],
        },
        {
          title: "Zakres usługi",
          body: [
            "Agent OZE jest asystentem sprzedaży dla rynku OZE. Usługa pomaga użytkownikowi zapisywać klientów, notatki, spotkania, zdjęcia, follow-upy i oferty w narzędziach Google użytkownika.",
            "Usługa składa się z panelu webowego, bota Telegram, backendu API oraz integracji z Google Sheets, Google Calendar, Google Drive i Gmail.",
            "Publiczny regulamin dotyczy każdego użytkownika zakładającego konto. Konta dla zespołów sprzedażowych, właścicieli firm OZE i klientów enterprise mogą wymagać osobnej umowy B2B podpisanej poza tym regulaminem.",
          ],
        },
        {
          title: "Konto użytkownika",
          bullets: [
            "Użytkownik zakłada konto w panelu Agent OZE i odpowiada za prawdziwość danych podanych podczas rejestracji.",
            "Dostęp do konta może wymagać aktywnej subskrypcji, okresu próbnego albo dostępu beta przyznanego przez operatora.",
            "Użytkownik odpowiada za bezpieczeństwo własnego konta email, konta Google i konta Telegram.",
            "Nie wolno udostępniać konta osobom, które nie są uprawnione do pracy na danych klientów użytkownika.",
          ],
        },
        {
          title: "Subskrypcja i płatności",
          bullets: [
            "Dostęp płatny jest rozliczany w modelu subskrypcyjnym zgodnie z ceną widoczną w panelu płatności przed zakupem.",
            "Okres próbny, jeśli jest dostępny, działa na zasadach pokazanych w procesie onboardingu.",
            "Obsługa płatności może być realizowana przez zewnętrznego operatora płatności. Agent OZE nie przechowuje pełnych danych karty płatniczej.",
            "Subskrypcja może odnawiać się automatycznie, jeśli tak wynika z informacji pokazanej przy płatności. Użytkownik może zrezygnować zgodnie z opcjami dostępnymi w panelu albo przez kontakt ze wsparciem.",
            `Pytania o faktury, płatności i rozliczenia należy kierować na ${BILLING_EMAIL}.`,
          ],
        },
        {
          title: "Rozpoczęcie usługi cyfrowej i odstąpienie",
          body: [
            "Jeżeli użytkownik jest konsumentem albo korzysta z ochrony podobnej do konsumenckiej, przysługują mu obowiązkowe prawa wynikające z przepisów prawa, w tym prawo odstąpienia, jeśli ma zastosowanie.",
            "Jeżeli użytkownik chce korzystać z usługi cyfrowej od razu, przed upływem ustawowego terminu odstąpienia, możemy wymagać wyraźnej zgody na rozpoczęcie świadczenia usługi cyfrowej przed upływem terminu odstąpienia oraz potwierdzenia przyjęcia do wiadomości skutków takiej zgody.",
            "obowiązkowe prawa konsumenta pozostają nadrzędne wobec regulaminu.",
            "Nie ograniczamy obowiązkowych praw konsumenta. Postanowienia ograniczające odpowiedzialność lub roszczenia stosuje się tylko w zakresie dopuszczalnym przez prawo.",
          ],
        },
        {
          title: "Google",
          bullets: [
            "Połączenie Google jest wymagane do działania CRM, kalendarza, zdjęć i wysyłki ofert.",
            "Użytkownik udziela dostępu przez Google OAuth i może go cofnąć w ustawieniach konta Google.",
            "Dane CRM pozostają na koncie Google użytkownika. Arkusze, kalendarze, foldery i wiadomości należą do użytkownika.",
            "Agent OZE wykonuje operacje w Google tylko w zakresie funkcji produktu i zgodnie z potwierdzeniami użytkownika w aplikacji lub bocie.",
          ],
        },
        {
          title: "Telegram i Gmail",
          bullets: [
            "Bot Telegram służy do szybkiego zapisu i odczytu informacji sprzedażowych oraz do potwierdzania wybranych działań.",
            "Mutacje w Google Sheets, Google Calendar i Google Drive wymagają świadomego potwierdzenia użytkownika, zgodnie z zasadami produktu.",
            "Wysyłka oferty przez Gmail następuje dopiero po osobnym potwierdzeniu użytkownika w flow ofertowym.",
            "Użytkownik odpowiada za treść wysyłanych ofert, poprawność danych klienta i zgodność komunikacji handlowej z prawem.",
          ],
        },
        {
          title: "Obowiązki użytkownika",
          bullets: [
            "Użytkownik powinien mieć prawo do przetwarzania danych klientów, które wprowadza do Agent OZE i Google.",
            "Użytkownik odpowiada za zgodność swoich działań sprzedażowych z prawem, w tym za podstawę kontaktu z klientami, treść ofert, zgody marketingowe i obowiązki informacyjne wobec własnych klientów.",
            "Użytkownik nie może używać usługi do spamu, nękania, naruszania prawa ani wysyłania treści wprowadzających w błąd.",
            "Użytkownik powinien kontrolować poprawność danych zapisywanych przez bota, szczególnie przed wysłaniem oferty lub zapisaniem spotkania.",
            "Użytkownik powinien regularnie sprawdzać własne zasoby Google, ponieważ są źródłem prawdy dla danych CRM.",
          ],
        },
        {
          title: "Uprawnienia operatora",
          bullets: [
            "Możemy zawiesić lub ograniczyć konto w razie braku płatności, nadużyć, naruszenia prawa, ryzyka bezpieczeństwa, naruszenia regulaminu albo działań zagrażających usłudze lub innym użytkownikom.",
            "Możemy zmienić cennik, funkcje, limity, modele AI i sposób działania usługi, informując użytkowników z rozsądnym wyprzedzeniem, gdy zmiana istotnie wpływa na aktywną usługę.",
            "Możemy udostępniać wersje beta, eksperymentalne lub testowe. Takie funkcje mogą działać niestabilnie, zmieniać się albo zostać wycofane.",
            "Możemy analizować użycie produktu, koszty AI, błędy, feedback i wzorce workflow, aby poprawiać usługę, rozwijać funkcje i tworzyć zagregowane benchmarki.",
            "Możemy używać feedbacku, sugestii i zgłoszeń użytkownika do rozwoju produktu bez odrębnego wynagrodzenia za pomysł. Publiczne case studies, logo i referencje wymagają osobnej zgody albo osobnej umowy.",
          ],
        },
        {
          title: "Dostępność i zmiany usługi",
          body: [
            "Dokładamy starań, aby usługa była dostępna stabilnie, ale nie gwarantujemy nieprzerwanego działania. Integracje zależą także od Google, Telegram, Supabase, Stripe i innych dostawców infrastruktury.",
            "Możemy zmieniać funkcje, interfejs, ceny i zakres usługi. Zmiany istotne dla aktywnych użytkowników komunikujemy z rozsądnym wyprzedzeniem, o ile jest to możliwe.",
          ],
        },
        {
          title: "Odpowiedzialność",
          bullets: [
            "Agent OZE wspiera proces sprzedaży, ale nie zastępuje decyzji biznesowych użytkownika.",
            "Użytkownik odpowiada za finalną weryfikację danych klienta, terminów, treści ofert i wysyłanych wiadomości.",
            "Nie odpowiadamy za utratę danych wynikającą z działań użytkownika w jego własnym koncie Google, cofnięcia dostępu, usunięcia zasobów albo awarii po stronie zewnętrznych dostawców.",
            "Wobec konsumentów i osób korzystających z obowiązkowej ochrony konsumenckiej nie ograniczamy odpowiedzialności w zakresie, w jakim prawo tego zakazuje.",
            "Wobec użytkowników biznesowych odpowiedzialność operatora jest ograniczona w maksymalnym zakresie dozwolonym przez prawo właściwe dla danej relacji z użytkownikiem, w szczególności za utracone korzyści, pośrednie szkody biznesowe i decyzje sprzedażowe użytkownika.",
          ],
        },
        {
          title: "Rezygnacja, odstąpienie i usunięcie konta",
          bullets: [
            "Użytkownik może zrezygnować z subskrypcji zgodnie z opcjami dostępnymi w panelu płatności albo kontaktując się ze wsparciem.",
            "Jeśli użytkownikowi przysługuje ustawowe prawo odstąpienia, może z niego skorzystać na zasadach wynikających z obowiązujących przepisów.",
            `Prośby o usunięcie konta lub pomoc w odłączeniu Google należy kierować na ${SUPPORT_EMAIL}.`,
            "Rezygnacja z Agent OZE nie usuwa automatycznie danych z Google użytkownika. Użytkownik może zachować albo usunąć je samodzielnie w Google.",
          ],
        },
        {
          title: "Kontakt i reklamacje",
          body: [
            `Zgłoszenia techniczne, reklamacje i pytania dotyczące konta należy wysyłać na ${SUPPORT_EMAIL}. W zgłoszeniu warto podać adres email konta, opis problemu i zrzuty ekranu, jeśli pomagają wyjaśnić sytuację.`,
            "Reklamacje rozpatrujemy w rozsądnym terminie, a w przypadku użytkowników objętych obowiązkową ochroną konsumencką zgodnie z terminami wymaganymi przez właściwe przepisy.",
          ],
        },
      ]}
    />
  );
}
