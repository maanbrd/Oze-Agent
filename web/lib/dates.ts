export function warsawDateKey(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Warsaw",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);

  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

export function warsawDateKeyFromIso(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return warsawDateKey(date);
}

export function formatWarsawDayLabel(dayKey: string) {
  const [year, month, day] = dayKey.split("-").map(Number);
  if (!year || !month || !day) return dayKey;

  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: "Europe/Warsaw",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    weekday: "long",
  }).format(new Date(Date.UTC(year, month - 1, day, 12)));
}

export function formatWarsawTime(value: string) {
  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: "Europe/Warsaw",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
