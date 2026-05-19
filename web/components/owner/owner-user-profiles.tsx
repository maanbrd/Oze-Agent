import Link from "next/link";
import type { OwnerUserProfile, OwnerUserProfilesData } from "@/lib/api/admin-user-profiles";
import { OwnerPanel, QualityBadge } from "@/components/owner/owner-dashboard";

export function OwnerUserProfilesDashboard({
  data,
  selectedProfile = null,
  detailError = null,
}: {
  data: OwnerUserProfilesData;
  selectedProfile?: OwnerUserProfile | null;
  detailError?: string | null;
}) {
  const profiles = data.profiles;
  const selected = selectedProfile ?? profiles[0] ?? null;
  const okCount = profiles.filter((profile) => profile.status === "ok").length;
  const failedCount = profiles.filter((profile) => profile.status === "failed").length;
  const messagesCount = profiles.reduce((sum, profile) => sum + Number(profile.analyzed_messages_count || 0), 0);

  return (
    <OwnerPanel
      title="Profile użytkowników"
      description="Wewnętrzne profile pracy handlowców, generowane automatycznie z rozmów w Telegramie. To warstwa obserwacyjna, bez wpływu na runtime agenta."
    >
      {data.error || detailError ? (
        <div className="rounded-[8px] border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
          {data.error || detailError}
        </div>
      ) : null}

      <section className="grid gap-3 md:grid-cols-4">
        <Metric label="Profile" value={profiles.length} detail="użytkowników z wygenerowanym profilem" />
        <Metric label="OK" value={okCount} detail="ostatni przebieg bez błędu" />
        <Metric label="Błędy" value={failedCount} detail="profile wymagające sprawdzenia" warn />
        <Metric label="Wiadomości" value={messagesCount} detail="ostatnio analizowane rozmowy" />
      </section>

      <section className="grid gap-3 xl:grid-cols-[360px_1fr]">
        <article className="rounded-[8px] border border-white/10 bg-white/[0.025] p-4">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-sm font-semibold text-white">Użytkownicy</h2>
            <p className="text-[11px] text-zinc-500">ostatni profil na górze</p>
          </div>
          <div className="mt-4 grid gap-2">
            {profiles.length > 0 ? (
              profiles.map((profile) => (
                <ProfileListItem
                  key={profile.user_id}
                  profile={profile}
                  active={selected?.user_id === profile.user_id}
                />
              ))
            ) : (
              <p className="rounded-[8px] border border-white/10 bg-black/25 p-3 text-sm text-zinc-500">
                Brak profili. Dane pojawią się po pierwszym nocnym przebiegu agenta profilującego.
              </p>
            )}
          </div>
        </article>

        <article className="rounded-[8px] border border-white/10 bg-white/[0.025] p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Markdown profilu</h2>
              <p className="mt-1 text-xs text-zinc-500">
                {selected ? `${selected.name || selected.email || selected.user_id}` : "Brak wybranego profilu"}
              </p>
            </div>
            {selected ? <StatusBadge status={selected.status} /> : null}
          </div>
          {selected ? (
            <div className="mt-4 grid gap-3 xl:grid-cols-[1fr_320px]">
              <pre className="max-h-[720px] overflow-auto whitespace-pre-wrap rounded-[8px] border border-white/10 bg-black/35 p-4 text-sm leading-6 text-zinc-200">
                {selected.profile_markdown}
              </pre>
              <aside className="rounded-[8px] border border-white/10 bg-black/25 p-4">
                <h3 className="text-sm font-semibold text-white">Wnioski</h3>
                <dl className="mt-4 grid gap-3 text-sm">
                  <Meta label="Ostatnia analiza" value={formatDateTime(selected.last_run_at)} />
                  <Meta label="Ostatnia wiadomość" value={formatDateTime(selected.last_analyzed_message_at)} />
                  <Meta label="Wiadomości" value={String(selected.analyzed_messages_count || 0)} />
                  <Meta label="Model" value={selected.model || "brak danych"} />
                  <Meta label="Koszt" value={`$${Number(selected.cost_usd || 0).toFixed(4)}`} />
                </dl>
                {selected.error ? (
                  <p className="mt-4 rounded-[8px] border border-amber-300/25 bg-amber-300/10 p-3 text-xs leading-5 text-amber-100">
                    {selected.error}
                  </p>
                ) : null}
                <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap rounded-[8px] border border-white/10 bg-black/35 p-3 text-xs leading-5 text-zinc-400">
                  {JSON.stringify(selected.insights_json, null, 2)}
                </pre>
              </aside>
            </div>
          ) : (
            <p className="mt-4 rounded-[8px] border border-white/10 bg-black/25 p-4 text-sm text-zinc-500">
              Profilujący agent zapisze tutaj markdown i JSON z wnioskami po pierwszym przebiegu.
            </p>
          )}
        </article>
      </section>
    </OwnerPanel>
  );
}

function ProfileListItem({
  profile,
  active,
}: {
  profile: OwnerUserProfile;
  active: boolean;
}) {
  return (
    <Link
      href={`/admin/profile-uzytkownikow?userId=${encodeURIComponent(profile.user_id)}`}
      className={
        active
          ? "block rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 p-3"
          : "block rounded-[8px] border border-white/10 bg-black/25 p-3 transition hover:border-white/20 hover:bg-white/[0.04]"
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white">{profile.name || profile.email || profile.user_id}</p>
          <p className="mt-1 truncate text-xs text-zinc-500">{profile.email || `Telegram ${profile.telegram_id ?? "-"}`}</p>
        </div>
        <StatusBadge status={profile.status} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-zinc-500">
        <span>{formatDateTime(profile.last_run_at)}</span>
        <span>{profile.analyzed_messages_count || 0} wiadomości</span>
      </div>
    </Link>
  );
}

function Metric({
  label,
  value,
  detail,
  warn = false,
}: {
  label: string;
  value: number;
  detail: string;
  warn?: boolean;
}) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-white/[0.025] p-4">
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">{label}</p>
      <p className={warn ? "mt-2 text-3xl font-semibold text-amber-300" : "mt-2 text-3xl font-semibold text-[#3DFF7A]"}>
        {value.toLocaleString("pl-PL")}
      </p>
      <p className="mt-2 text-xs leading-5 text-zinc-500">{detail}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "ok") {
    return <QualityBadge quality="real" />;
  }
  return (
    <span className="rounded-full border border-amber-300/25 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-200">
      {status || "brak"}
    </span>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-[0.16em] text-zinc-600">{label}</dt>
      <dd className="mt-1 break-words text-zinc-300">{value}</dd>
    </div>
  );
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "brak danych";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Europe/Warsaw",
  }).format(date);
}
