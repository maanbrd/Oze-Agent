# Webapp Loading & Feedback Visual Language — Design Spec

_Date: 2026-05-29_
_Status: Approved, ready for implementation plan_
_Audit reference: `~/.claude/plans/to-czego-zdecydowanie-teraz-golden-kay.md`_

---

## Context

Maan zgłosił, że w lejku konwersji Agent-OZE (rejestracja → płatność → OAuth → tworzenie zasobów Google → Telegram) są momenty 1–10 sekund ciszy, w których użytkownik nie ma żadnego potwierdzenia, że jego kliknięcie zostało zarejestrowane. Powoduje to double-clicks → zduplikowane sesje, race conditions, drop-off.

Poprzedni krok (audyt) zinwentaryzował 6 typów artefaktów wizualnych do zaprojektowania. Ten dokument zamyka warstwę projektową: ustala kanoniczny wygląd, animacje, kontrakty i pliki, na podstawie których powstanie plan implementacji. **Sam dokument nie zmienia kodu** — to wejście do następnego kroku (writing-plans).

## Goals

1. Każde kliknięcie z czasem odpowiedzi >150 ms ma widoczny feedback w ≤100 ms od momentu kliknięcia.
2. Każda operacja >2 s ma feedback informujący o naturze ciszy (spinner, skeleton, progress, status text).
3. Każda destrukcyjna lub long-running operacja ma feedback informujący o jej zakończeniu (toast).
4. Visual language jest spójny z brand'em z landingu (outline-only `#3DFF7A` na `#0b0d10`, lowercase typography, małe ruchome elementy) — żaden nowy artefakt nie wygląda jak generyczny shadcn/Lucide spinner.
5. Wszystkie animacje respektują `prefers-reduced-motion: reduce` — fallback to statyczny stan.

## Non-Goals

- Nie projektujemy nowych typograficznych tokens, nie refaktorujemy istniejącego dark theme.
- Nie zmieniamy zachowania backendu w istniejących server actions (poza dodaniem 1 nowego endpointu progress dla zasobów Google — patrz §5).
- Nie ruszamy panelu `/admin/*` i stron `*-preview` (poza scope, druga runda).
- Nie wprowadzamy `<NavigationProgress />` na linkach Next.js (P3, odrębna decyzja).

## Acceptance Criteria

System wizualny jest uznany za działający, gdy:

1. **Slow network test** (Chrome DevTools, „Slow 3G"): każdy formularz w P1 z audytu pokazuje spinner w <100 ms od kliknięcia.
2. **Double-click test**: każdy form button klikany 3× w sekundę produkuje dokładnie 1 request w Network tab.
3. **Cancel test**: Esc / wstecz w trakcie nawigacji nie zostawia zawieszonego spinnera.
4. **Reduced-motion test**: `prefers-reduced-motion: reduce` w DevTools wyłącza wszystkie keyframe animations, zostawia statyczny stan z aktywnym kolorem.
5. **CLS test** (Lighthouse): dodanie skeletonów nie pogarsza Cumulative Layout Shift.
6. **Realny test akceptacyjny**: Maan klika rejestrację → płatność na koncie testowym i nie ma odruchu kliknięcia drugi raz.

---

## 1. Visual Tokens (brand-locked)

Wszystkie komponenty używają tylko poniższego zestawu — nie wprowadzamy nowych kolorów ani innych grubości strokeów.

| Token | Wartość | Zastosowanie |
|---|---|---|
| `--brand-green` | `#3DFF7A` | wszystkie active outlines, glow, akcenty |
| `--brand-bg` | `#0b0d10` | tło kart, buttonów, kanwy |
| `--brand-bg-deep` | `#050607` | tło sceny / pełne ekrany |
| `--brand-bg-inset` | `#060709` | tło dla embedded sekcji (np. header'y stage) |
| `--ui-border-dim` | `#1f242b` | nieaktywne ramki, rails dashed line |
| `--ui-text-primary` | `#f5f7fa` | główny tekst |
| `--ui-text-muted` | `#6b7280` | subtitle, eyebrow, labels nieaktywne |
| `--ui-text-deep` | `#4a5460` | inactive step labels |
| `--state-error` | `#FF6464` | toast error, retry button |
| `--state-neutral` | `#9aa5b1` | toast info |

Stroke: zawsze `1.5px` (skeleton, ikony, pierścień spinnera) lub `1.4px` (cienkie connectory, breadcrumb arrow).
Glow: `box-shadow: 0 0 18px #3DFF7A22` (low intensity), `0 0 22px #3DFF7A55` (active breathe peak), `drop-shadow(0 0 4px #3DFF7A88)` (SVG).
Border radius: `12–14px` (cards, buttons), `999px` (pills, CTAs).

## 2. Wzorzec A — Mini-spinner („Pierścień rozwijający")

SVG circle outline z animowanym `stroke-dasharray` + rotacja całego SVG. Czyta się jak ciągle rozwijająca/zwijająca się linia.

**Spec**:
- Wymiary: `22 × 22px` (button-level), `26 × 26px` w wariancie standalone (3-step ikony).
- Solid (na zielonym CTA): stroke `#0b0d10`, brak glow.
- Outline (na ciemnym buttonie): stroke `#3DFF7A`, `drop-shadow(0 0 4px #3DFF7A88)`.
- Animacja A1 — rotacja całego SVG: 1.2 s linear infinite.
- Animacja A2 — `stroke-dasharray` 1.6 s ease-in-out infinite (keyframes: `5 120 → 80 45 → 5 120`, `stroke-dashoffset: 0 → -30 → -125`).
- `prefers-reduced-motion: reduce`: brak rotacji, brak dash animacji, statyczny pierścień `stroke-dasharray: 50 70`, kolor brand green.

**Użycie**: w każdym `<SubmitButton pendingLabel="…" />` (uniwersalny komponent), wewnątrz buttonów onClick z lokalnym `isLoading` w `/oferty`.

**Komponent**: `web/components/ui/brand-spinner.tsx` + `web/components/ui/submit-button.tsx`.

## 3. Wzorzec B — Strzałka header bar (page transition)

Dwa współpracujące elementy w nagłówku strony podczas nawigacji do nowej trasy:

1. **Sliding rail** — 3 px wysoki pasek na samej górze viewportu, `#1f242b` background, w środku przesuwający się gradient `transparent → #3DFF7A → transparent` z `box-shadow: 0 0 12px #3DFF7A88`. Animacja: `left: -40% → 100%`, 1.4 s `cubic-bezier(.65,.05,.36,1)` infinite.
2. **Breadcrumb crawl** (opcjonalne, tam gdzie jest sensowny breadcrumb): SVG strzałka horizontal, dwie ścieżki — `dash-line` (`stroke-dasharray: 5 6`, animowany `stroke-dashoffset` 0.8 s linear infinite, czyta się jak crawling ants) + statyczny head strzałki.

**Spec stroke**: `#3DFF7A`, `1.4px`, `drop-shadow(0 0 4px #3DFF7A77)`.

**Trigger**: globalny, montowany w `app/layout.tsx` przez wrapper słuchający `useLinkStatus()` (Next.js 15) + ręcznie wymuszany przez server actions, które wykonują `redirect()`.

**`prefers-reduced-motion`**: rail zatrzymany w środku jako statyczny segment `#3DFF7A`; breadcrumb crawl bez animacji, stała dashed line.

**Komponent**: `web/components/ui/navigation-bar.tsx` + `web/components/ui/breadcrumb-arrow.tsx`.

## 4. Wzorzec C — Outline skeleton

Loader.tsx per segment Next.js App Routera — outline-only ramki z pulsującym borderem.

**Spec**:
- Każdy element to outline `<div>` z `border: 1.5px solid #3DFF7A`, `border-radius: 6px` (linie tekstu) lub `999px` (CTA pill).
- Pulsująca animacja: `1.6 s ease-in-out infinite`, keyframes — `border-color: #3DFF7A22 (boxshadow: none) → #3DFF7A (boxshadow: 0 0 8px #3DFF7A44) → #3DFF7A22`.
- Stagger animacji: kolejne elementy z `animation-delay: 0.15 s, 0.30 s, 0.45 s, 0.60 s` (peak biegnie z góry na dół).
- Layout: skeleton musi rezerwować dokładnie tę samą wysokość i padding co realny render — żeby uniknąć CLS po hydration.

**Lokacje**:
- `web/app/onboarding/platnosc/loading.tsx`
- `web/app/onboarding/google/loading.tsx`
- `web/app/onboarding/zasoby/loading.tsx`
- `web/app/(app)/dashboard/loading.tsx`
- `web/app/(app)/klienci/loading.tsx`
- `web/app/(app)/kalendarz/loading.tsx`

**`prefers-reduced-motion`**: brak `animation`, stały `border-color: #3DFF7A55` (subtle hint).

**Komponent**: `web/components/ui/skeleton.tsx` — `<SkeletonLine variant="title|sub|body|cta" />`. Można też `<SkeletonCard>` jako container z presetami.

## 5. Wzorzec D — 3-step progress dla `createGoogleResources`

Showcase'owy element: 3 outline ikony (Sheets / Kalendarz / Drive) połączone strzałka crawl, każda w jednym z 3 stanów: `pending` / `active` / `done`.

**Spec**:
- Każdy step: `56 × 56px` ikona-frame, border `1.5px`, padding 14 px. SVG ikona `26 × 26px` w środku.
- **`pending`**: border `#1f242b`, stroke ikony `#4a5460`, label `#6b7280`.
- **`active`**: border `#3DFF7A`, stroke ikony `#3DFF7A`, label `#3DFF7A`, breathe animacja 1.6 s — `box-shadow` oscyluje między `0 0 0 1px #3DFF7A33, 0 0 12px #3DFF7A33` a `0 0 0 1px #3DFF7A88, 0 0 26px #3DFF7A66`.
- **`done`**: border `#3DFF7A`, stroke ikony `#3DFF7A`, `box-shadow: 0 0 0 1px #3DFF7A33` (stały), label `#f5f7fa`, dodatkowy checkmark badge `18 × 18px` w prawym dolnym rogu (zielony background `#3DFF7A`, czarny `✓`, fade-in 200 ms).
- Connectors między stepami: dwie ścieżki SVG — `rail` (`stroke: #1f242b`, `stroke-dasharray: 4 5`) + `crawl` widoczny tylko gdy następny step jest `active` (`stroke: #3DFF7A`, `stroke-dasharray: 5 6`, animowany `stroke-dashoffset` 0.8 s linear) + head strzałki widoczny tylko po `done`.
- Layout: poziomy (3 steps + 2 connectors), centered, `max-width: 560px`.
- Pod stepami: status text z animowanymi kropkami ("Konfiguruję Twój kalendarz...") + elapsed time uppercase ("UPŁYNĘŁO 18 s", liczba w `#3DFF7A`).
- Reasekuracja u dołu: italic muted text "Operacja jest jednorazowa — robimy ją raz na całe życie konta.".
- Po `done` na wszystkich krokach: status text "Gotowe — przekierowuję", redirect po 800 ms do `/onboarding/telegram`.

**Backend kontrakt**:
- Endpoint: `GET /api/onboarding/resources-progress` — SSE strumień lub polling co 2 s.
- Payload: `{ step: "sheets" | "calendar" | "drive" | "done", elapsed_ms: number, error?: { code: string, message: string } }`.
- Implementacja po stronie FastAPI: state writeback do Supabase `onboarding_progress` table (klucz: user_id), webapp czyta przez webhook lub polling. Szczegóły protokołu (SSE vs polling) → decyzja w pliku implementacji, nie tutaj.

**`prefers-reduced-motion`**: brak breathe, brak crawl, brak fade-in checkmarka; statyczne 3 stany, kolory zostają.

**Komponent**: `web/components/onboarding/resource-progress.tsx`. Zastępuje obecny `<ResourceSubmitButton>` po kliknięciu submit (button znika, pojawia się 3-step canvas).

## 6. Wzorzec E — Toast (sonner z brand theme)

Globalny system toastów oparty na bibliotece [sonner](https://sonner.emilkowal.ski) z brand-locked theme.

**Warianty**:
- **Success**: border `#3DFF7A`, ikona okrąg outline `#3DFF7A` z `✓` w środku, `box-shadow: 0 0 18px #3DFF7A22, 0 12px 36px #00000088`.
- **Error**: border `#FF6464`, ikona z `!`, retry/dismiss buttons; podobny glow ale w czerwonej palecie.
- **Info / action**: border `#9aa5b1`, ikona z `⤺` (undo) lub `ℹ`.

**Wszystkie warianty mają**:
- Background `#0b0d10`, padding `14px 16px 16px`, border-radius `12px`, font-size 13 px.
- Title (medium weight) + opcjonalny body (12 px, `#9ca3af`, line-height 1.5).
- Opcjonalne `actions` — przyciski text-only, uppercase, letter-spacing 0.04 em, kolor matching border (zielony / czerwony / muted).
- Countdown bar u dołu: 2 px wysoka, drain animacja `right: 0 → right: 100%` w czasie TTL.

**TTL**:
- Success: 6 s.
- Error: 8 s.
- Action (z Undo): 6 s. Klik na „Cofnij" anuluje TTL i wywołuje undo callback.

**Pozycja**: bottom-right viewportu, stack vertical, gap 12 px, max-width 340 px.

**`prefers-reduced-motion`**: brak enter/exit animacji (fade-in/slide), TTL bar bez animacji (statyczna pełna szerokość).

**API**:
```typescript
// web/lib/ui/toast.ts
import { toast } from "sonner";

export const showSuccess = (title: string, body?: string) =>
  toast.success(title, { description: body, duration: 6000 });

export const showError = (title: string, body?: string, retry?: () => void) =>
  toast.error(title, {
    description: body,
    duration: 8000,
    action: retry ? { label: "Spróbuj ponownie", onClick: retry } : undefined,
  });

export const showAction = (
  title: string,
  body: string,
  undo: () => void
) =>
  toast(title, {
    description: body,
    duration: 6000,
    action: { label: "Cofnij", onClick: undo },
  });

// Promise wrapper dla async actions
export const showPromise = <T,>(
  promise: Promise<T>,
  msgs: { loading: string; success: string; error: string }
) => toast.promise(promise, msgs);
```

**Globalna instancja**: `<Toaster theme="dark" />` w `web/app/layout.tsx` z custom CSS dla brand theme (sonner przyjmuje `toastOptions.classNames`).

**Migracja**: istniejący custom toast z `web/components/dashboard/decyzje-preview.tsx` (linie 27–47, 310–350) jest źródłem stylowania, ale w docelowym kodzie używamy sonner z helperami powyżej. Custom toast zostaje jako reference, nie jest duplikowany.

## 7. Wzorzec F — Interstitial dla redirect chains

Nowa strona pośrednia, montowana dla 3 konkretnych redirectów >1 s.

**Route**: `/onboarding/przekierowuje?to=stripe|google|next`.

**Layout**: pełnoekranowa kanwa z radial-gradient background (`#0b0d10` w środku → `#050607` na krawędziach), centered content.

**Komponent**:
- **Brand mark** na górze — okrąg outline `#3DFF7A` 36 × 36 px, w środku dot `#3DFF7A` 10 × 10 px z breathing animacją 2.2 s (opacity 0.55 → 1, scale 0.9 → 1.1, ease-in-out).
- **Status text** ("Otwieram Stripe..." z animowanymi kropkami).
- **Subtitle** (11 px muted, np. "Za chwilę przeniesiemy Cię do bezpiecznej płatności.").
- **Pill steps row** — 3 pill-shaped labels (76 px max width) z connector dash:
  - `done`: border `#3DFF7A66`, text `#3DFF7A`.
  - `active`: border `#3DFF7A`, text `#3DFF7A`, breathe glow `box-shadow` jak w 3-step progress.
  - `pending`: border `#1f242b`, text `#4a5460`.
  - Connectors: identyczna logika jak 3-step (crawl dash dla aktywnego segmentu, statyczny dim dla pending).

**Kiedy montowany**:
1. Po kliknięciu „Rozpocznij 3 dni testu" / „Kontynuuj jako beta tester" w `/onboarding/platnosc` — server action `createCheckoutSession` lub `activateBetaAccess` najpierw `redirect("/onboarding/przekierowuje?to=stripe")`, ten ekran montuje się, w `useEffect` rozpoczyna prawdziwy redirect po 600 ms (pozwala na 1 frame renderu).
2. Analogicznie dla `startGoogleOAuthAction` → `?to=google`.
3. Po Google OAuth callback w `/onboarding/google/sukces` → `?to=next` przed redirect do `/onboarding/zasoby`.

**Steps copy per route**:
- `?to=stripe`: `Konto` (done) → `Stripe` (active) → `Płatność` (pending).
- `?to=google`: `Konto` (done) → `Google` (active) → `Uprawnienia` (pending).
- `?to=next`: `Google` (done) → `Sprawdzam` (active) → `Zasoby` (pending).

**`prefers-reduced-motion`**: brand mark statyczny (bez breathe), pill steps bez glow oscylacji, connector dash statyczny.

**Komponent**: `web/components/ui/redirecting-screen.tsx` przyjmujący `steps: { label: string; status: "done"|"active"|"pending" }[]` i `nextUrl: string`. Page wrapper: `web/app/onboarding/przekierowuje/page.tsx` parsuje query param i wybiera odpowiednie steps.

## 8. Accessibility — `prefers-reduced-motion`

Każda animacja CSS w tym specu MUSI być opakowana w `@media (prefers-reduced-motion: reduce)` z reset rules (patrz wcześniejsze sekcje per wzorzec). Globalny helper:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
```

— ale to za szerokie. Per-wzorzec rezolucja w komponentach pozwala kontrolować, co dokładnie zostaje statyczne (np. kolor aktywnego stepa MUSI zostać, mimo że animacja breathe znika).

Dodatkowo:
- Każdy spinner ma `role="status"` + `aria-live="polite"` + `<span class="sr-only">` z pendingLabel.
- 3-step progress canvas ma `role="status"` + dynamicznie aktualizowany `aria-label="Krok 2 z 3: konfiguruję kalendarz, upłynęło 18 sekund"`.
- Toast: sonner ma wbudowane a11y (`aria-live`, focus management).

## 9. Pliki do utworzenia / zmodyfikowania

**Komponenty UI (nowe)**:
- `web/components/ui/brand-spinner.tsx` — Wzorzec A
- `web/components/ui/submit-button.tsx` — wrapper z `useFormStatus()` + brand-spinner
- `web/components/ui/navigation-bar.tsx` — Wzorzec B (sliding rail)
- `web/components/ui/breadcrumb-arrow.tsx` — Wzorzec B (crawling arrow)
- `web/components/ui/skeleton.tsx` — Wzorzec C
- `web/components/onboarding/resource-progress.tsx` — Wzorzec D
- `web/components/ui/redirecting-screen.tsx` — Wzorzec E

**Infra (nowe)**:
- `web/lib/ui/toast.ts` — helpery sonner
- `web/app/onboarding/przekierowuje/page.tsx` — interstitial route
- `web/app/api/onboarding/resources-progress/route.ts` — SSE/polling endpoint
- `web/app/onboarding/platnosc/loading.tsx`
- `web/app/onboarding/google/loading.tsx`
- `web/app/onboarding/zasoby/loading.tsx`
- `web/app/(app)/dashboard/loading.tsx`
- `web/app/(app)/klienci/loading.tsx`
- `web/app/(app)/kalendarz/loading.tsx`

**Modyfikacje (wymiana submit buttonów)**:
- `web/app/rejestracja/page.tsx`
- `web/app/login/page.tsx`
- `web/app/onboarding/platnosc/page.tsx`
- `web/app/onboarding/google/page.tsx`
- `web/app/(app)/ustawienia/page.tsx`
- `web/app/(app)/platnosci/page.tsx`
- `web/components/logout-button.tsx`
- `web/components/onboarding/telegram-pairing-card.tsx` (button „Wygeneruj nowy kod")

**Modyfikacje (offer generator — 7 async onClick)**:
- `web/components/offers/offer-generator.tsx` — wymiana 7 buttonów (`createDraft`, `moveReady`, `duplicateOffer`, `deleteOffer`, `saveEditor`, `publishEditor`, `downloadPdf`) na buttony z lokalnym `isLoading` + spinner + toast po success/error; confirm dialog dla `deleteOffer`.

**Modyfikacje (server actions — interstitial chain)**:
- `web/app/auth/actions.ts` — `signup` redirectuje do `/onboarding/przekierowuje?to=stripe` zamiast `/onboarding/platnosc` (interstitial przejmie real redirect)
- `web/app/onboarding/actions.ts` — `createCheckoutSession`, `activateBetaAccess`, `startGoogleOAuthAction` używają interstitial

**Modyfikacje (layout)**:
- `web/app/layout.tsx` — montuje `<Toaster />` i `<NavigationBar />` globalnie

**Modyfikacje (dashboard refactor)**:
- `web/components/dashboard/decyzje-preview.tsx` — custom toast usunięty, podmieniony na helpery z `lib/ui/toast.ts`. Optimistic UI + Undo zostają (ten kod jest dobry).

**Wzorzec referencyjny — NIE zmieniać**:
- `web/components/onboarding/resource-submit-button.tsx` — zastąpiony przez `<SubmitButton>` + `<ResourceProgress>`, oryginał można usunąć po podmianie.
- `web/components/onboarding/telegram-pairing-card.tsx` — countdown timer + polling logic zostaje, tylko submit button podmieniany.

## 10. Decyzje

- **Sonner > custom toast** — biblioteka jest mała (~3 kB), ma wbudowane a11y, zarządzanie z-index i focus traps. Custom toast z `decyzje-preview` jest dobry stylowo, ale duplikowanie go w `lib/ui/toast.ts` to martwy kod.
- **Interstitial in** — pomimo dodania nowej strony pośredniej, redirect chains (3 miejsca P1) to dokładnie ten punkt, gdzie Maan poskarżył się na ciszę. Sam strzałka header + spinner w buttonie pokrywa ~50% problemu; interstitial domyka pozostałe 50%.
- **SSE > polling dla resources-progress** — preferowane, bo eliminuje 2 s opóźnienia per polling tick. Jeśli FastAPI nie supportuje SSE w czystej formie, fallback do polling co 2 s — decyzja per implementacja, nie tu.
- **Spinner Wzorzec A (pierścień), nie strzałka** — strzałka B żyje samodzielnie poza buttonem (page transition, connectors). Pierścień jest uniwersalny, czytelny w 22 px, działa w solid CTA.
- **`useFormStatus()` zamiast `useTransition()` dla form actions** — Wzorzec A montowany w `<SubmitButton>` korzysta z `useFormStatus()`, bo to natywny Next.js mechanizm dla `<form action={…}>`. `useTransition()` zostaje dla optimistic UI w mutacjach listy (zachowany w `decyzje-preview.tsx`).
- **Brand visual language → wszystkie 7 wzorców** — jedna estetyka (outline, brand green, glow), jeden zestaw animacji (rotate / dash crawl / pulse / breathe), jeden font weight (regular/medium). Spec nie pozostawia miejsca na "wariant alternatywny".

## 11. Otwarte pytania → brak

Wszystkie decyzje wizualne zalockowane podczas brainstormu (28.05.2026). Mockupy w `/.superpowers/brainstorm/.../content/` jako visual reference (NIE commitować do repo).

Spec wchodzi do `writing-plans` jako wejście do harmonogramu implementacji.
