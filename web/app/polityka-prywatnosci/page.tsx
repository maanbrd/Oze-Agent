import type { Metadata } from "next";
import { LegalPage } from "@/components/legal-page";
import { ADMIN_EMAIL, SUPPORT_EMAIL } from "@/components/brand";

export const metadata: Metadata = {
  title: "Polityka prywatności | Agent OZE",
  description:
    "Polityka prywatności Agent OZE, w tym zasady użycia danych Google OAuth.",
};

const googleScopes = [
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/calendar",
  "https://www.googleapis.com/auth/drive.file",
  "https://www.googleapis.com/auth/gmail.send",
];

export default function PrivacyPage() {
  return (
    <LegalPage
      title="Polityka prywatności"
      lead="Ta polityka wyjaśnia, jakie dane przetwarza Agent OZE, jak działa Google OAuth, jakie korzyści produktowe i analityczne możemy uzyskiwać z danych oraz jak użytkownik może cofnąć dostęp albo usunąć konto."
      effectiveDate="24.05.2026"
      sections={[
        {
          title: "Administrator danych",
          body: [
            `Administratorem danych jest GREAT MF LLC, EIN 36-5120312, 810 Pony Express Rd, Cheyenne, WY 82009, USA. GREAT MF LLC jest tymczasowym operatorem publicznej usługi Agent OZE do czasu przeniesienia lub uruchomienia obsługi przez polski podmiot.`,
            `W sprawach prywatności i danych osobowych kontakt: ${ADMIN_EMAIL}. W sprawach technicznych i dostępu do konta kontakt: ${SUPPORT_EMAIL}.`,
            "Agent OZE jest narzędziem dla sprzedawców i użytkowników rynku OZE. Usługa pomaga prowadzić bazę klientów, plan dnia, zdjęcia, notatki i wysyłkę ofert przez konto Google użytkownika.",
            "Polityka jest przygotowana z myślą o użytkownikach w Polsce i Europejskim Obszarze Gospodarczym, dlatego opisuje obowiązki informacyjne wynikające z RODO/GDPR.",
          ],
        },
        {
          title: "Jakie dane przetwarzamy",
          bullets: [
            "Dane konta: adres email, imię, nazwisko, telefon, status płatności, zgody i informacje potrzebne do onboardingu.",
            "Dane ankietowe: onboarding_survey, region działania, specjalizacja, doświadczenie w OZE i referral source, czyli informacja skąd użytkownik zna Agent OZE.",
            "Dane operacyjne: identyfikator Telegram, historia konwersacji z botem, pending state, techniczne logi działania i konfiguracja użytkownika.",
            "Dane CRM użytkownika: klienci, notatki, spotkania, zdjęcia i oferty pozostają w Google Sheets, Google Calendar, Google Drive i Gmail użytkownika.",
            "Dane ofert: szablony ofert, profil sprzedawcy, logo ofert i techniczny rejestr prób wysyłki przechowujemy w Supabase jako dane systemowe.",
            "Dane techniczne i analityczne: zdarzenia logowania, błędy, koszty AI, liczba interakcji, używane modele, typy akcji, admin mirror, metryki operacyjne i dane potrzebne do utrzymania usługi.",
            "Dane profilowania produktu: conversation_history używana do krótkoterminowej pamięci bota oraz user_behavior_profiles, czyli admin-only profil sposobu pracy użytkownika tworzony w celu poprawy produktu i wsparcia.",
          ],
        },
        {
          title: "Google OAuth",
          body: [
            "Połączenie Google jest dobrowolne, ale wymagane do działania podstawowych funkcji Agent OZE. Użytkownik loguje się bezpośrednio na stronie Google i sam zatwierdza zakresy dostępu. Agent OZE nie zna hasła do konta Google.",
            "Aktualnie aplikacja prosi o następujące zakresy OAuth:",
          ],
          bullets: [
            `${googleScopes[0]} — tworzenie, odczyt i aktualizacja arkusza CRM użytkownika w Google Sheets.`,
            `${googleScopes[1]} — tworzenie dedykowanego kalendarza, dodawanie działań sprzedażowych i odczyt planu dnia w Google Calendar.`,
            `${googleScopes[2]} — tworzenie i używanie folderów oraz plików utworzonych przez aplikację w Google Drive, w szczególności zdjęć klientów.`,
            `${googleScopes[3]} — wysyłka potwierdzonych ofert PDF z Gmaila użytkownika po kliknięciu akcji wysyłki.`,
          ],
        },
        {
          title: "Jak używamy danych Google",
          bullets: [
            "Używamy danych Google tylko do funkcji widocznych w produkcie: CRM, plan dnia, zdjęcia, notatki, follow-upy i wysyłka ofert.",
            "nie używamy danych Google API do reklam, retargetingu, oceny zdolności kredytowej, sprzedaży danych, budowania list reklamowych ani przekazywania brokerom danych.",
            "Nie używamy danych Google do trenowania modeli AI. Dane mogą być przetwarzane przez dostawców infrastruktury i modeli tylko w zakresie potrzebnym do wykonania funkcji wywołanej przez użytkownika.",
            "Dostęp pracowników lub wykonawców do danych użytkownika jest ograniczony do wsparcia technicznego, bezpieczeństwa, rozliczeń albo usunięcia awarii.",
            "Dane z Google mogą być używane do diagnostyki, bezpieczeństwa i wyjaśniania błędów użytkownikowi, ale nie do ukrytych celów marketingowych.",
          ],
        },
        {
          title: "Limited Use",
          body: [
            "Użycie i przekazywanie przez Agent OZE informacji otrzymanych z interfejsów API Google jest zgodne z Google API Services User Data Policy, w tym z wymaganiami Limited Use.",
            "Oznacza to w praktyce, że dane Google są używane w zakresie potrzebnym do działania funkcji wybranych przez użytkownika, utrzymania bezpieczeństwa, obsługi wsparcia i spełnienia wymogów prawnych. Nie używamy ich do niezależnych kampanii reklamowych ani do monetyzacji danych poza usługą.",
          ],
        },
        {
          title: "Analityka produktu i korzyści biznesowe",
          body: [
            "Agent OZE może analizować sposób korzystania z usługi, aby poprawiać produkt, ograniczać koszty AI, wykrywać tarcia w workflow i budować lepsze funkcje dla sprzedawców OZE.",
          ],
          bullets: [
            "Tworzymy zagregowane benchmarki i statystyki, np. popularność funkcji, typowe ścieżki onboardingu, wzorce użycia bota, koszty AI, skuteczność flows i problemy techniczne.",
            "Możemy prowadzić profilowanie sposobu pracy użytkownika na podstawie interakcji z botem i panelem, ale takie profilowanie nie wywołuje skutków prawnych ani podobnie istotnych skutków wobec użytkownika.",
            "Możemy używać feedbacku, sugestii i zgłoszeń użytkowników do rozwoju produktu bez osobnego wynagrodzenia za sam pomysł, o ile nie narusza to praw bezwzględnie obowiązujących.",
            "Publiczne case studies, referencje, nazwy firm, logo użytkownika lub cytaty marketingowe wymagają osobnej zgody użytkownika albo osobnej umowy.",
          ],
        },
        {
          title: "Gdzie przechowujemy dane",
          bullets: [
            "Dane CRM źródłowo mieszkają na koncie Google użytkownika: Sheets, Calendar, Drive i Gmail.",
            "Tokeny Google przechowujemy w Supabase w formie zaszyfrowanej. Dostęp do nich ma tylko backend potrzebny do działania usługi.",
            "Systemowe dane konta, subskrypcji, konfiguracji, pending state i ofert przechowujemy w Supabase.",
            "Logi techniczne mogą zawierać identyfikatory systemowe, znaczniki czasu i komunikaty błędów, ale nie powinny zawierać haseł ani tokenów dostępu.",
          ],
        },
        {
          title: "Odbiorcy danych i transfer poza EOG",
          body: [
            "odbiorcy danych to podmioty, które pomagają nam utrzymać i rozwijać usługę.",
            "Dane mogą trafiać do odbiorców, którzy pomagają nam świadczyć usługę: dostawców hostingu, bazy danych, płatności, analityki technicznej, komunikacji, modeli AI, Google, Telegram i narzędzi wsparcia.",
            "Ponieważ administratorem jest GREAT MF LLC, a część dostawców działa poza Europejskim Obszarem Gospodarczym, może dochodzić do transferu danych poza EOG. Stosujemy dostępne mechanizmy ochrony, w szczególności umowy powierzenia, standardowe klauzule umowne albo inne podstawy przewidziane przez RODO, gdy są wymagane.",
          ],
        },
        {
          title: "Okres przechowywania",
          body: [
            "okres przechowywania zależy od rodzaju danych, celu przetwarzania, wymogów prawnych oraz potrzeby obrony lub dochodzenia roszczeń.",
          ],
          bullets: [
            "Dane konta przechowujemy przez czas korzystania z usługi, a potem przez okres potrzebny do rozliczeń, dochodzenia roszczeń, obsługi reklamacji i obowiązków prawnych.",
            "Dane płatności i dokumenty rozliczeniowe przechowujemy przez okres wymagany przez prawo podatkowe i księgowe.",
            "conversation_history i profile pracy użytkownika przechowujemy tak długo, jak jest to potrzebne do działania, wsparcia i poprawy usługi, chyba że użytkownik skutecznie zażąda usunięcia wcześniej.",
            "Dane Google pozostają przede wszystkim na koncie Google użytkownika. Po odłączeniu Google usuwamy lub anonimizujemy zapisane tokeny i dane systemowe zgodnie z zasadami tej polityki.",
            "Zagregowane lub zanonimizowane statystyki, które nie pozwalają już zidentyfikować użytkownika, możemy przechowywać bezterminowo jako dane biznesowe i produktowe.",
          ],
        },
        {
          title: "Cofnięcie dostępu i usunięcie konta",
          bullets: [
            "Użytkownik może cofnąć dostęp Agent OZE do Google w ustawieniach konta Google, w sekcji połączonych aplikacji.",
            `Użytkownik może poprosić o usunięcie konta, pisząc na ${SUPPORT_EMAIL}. Po weryfikacji usuwamy lub anonimizujemy dane systemowe, o ile prawo nie wymaga ich dalszego przechowywania.`,
            "Usunięcie konta w Agent OZE nie usuwa automatycznie arkuszy, kalendarzy, folderów i wiadomości na koncie Google użytkownika. Te dane należą do użytkownika i można je usunąć bezpośrednio w Google.",
            "Po cofnięciu dostępu Google część funkcji przestaje działać do czasu ponownej autoryzacji.",
          ],
        },
        {
          title: "Podstawy przetwarzania",
          bullets: [
            "Wykonanie umowy: prowadzenie konta, subskrypcji, CRM, integracji Google i Telegram.",
            "Uzasadniony interes: bezpieczeństwo, diagnostyka błędów, obsługa wsparcia, zapobieganie nadużyciom, analityka produktu, admin mirror, optymalizacja kosztów AI, zagregowane benchmarki i rozwój usługi.",
            "Zgoda: komunikacja marketingowa, kontakt telefoniczny, case studies, wykorzystanie logo lub publiczna referencja, jeśli użytkownik wyraził takie zgody.",
            "Obowiązek prawny: rozliczenia, księgowość i odpowiedzi na uprawnione żądania organów.",
          ],
        },
        {
          title: "Prawa użytkownika",
          body: [
            `Użytkownik może poprosić o dostęp do danych, sprostowanie, ograniczenie przetwarzania, usunięcie danych, eksport danych, cofnięcie zgody marketingowej albo sprzeciw wobec przetwarzania. Kontakt: ${ADMIN_EMAIL}.`,
            "Użytkownik z EOG ma też prawo wnieść skargę do organu nadzorczego. W Polsce jest nim Prezes UODO.",
            "Cofnięcie zgody nie wpływa na zgodność z prawem przetwarzania dokonanego przed jej cofnięciem.",
          ],
        },
        {
          title: "Zmiany polityki",
          body: [
            "Możemy aktualizować tę politykę, gdy zmienia się produkt, prawo albo wymagania dostawców platform. Aktualna wersja jest zawsze dostępna publicznie pod tym adresem.",
          ],
        },
      ]}
    />
  );
}
