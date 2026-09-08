const MOMENTS = ["Midi", "Soir"];

const escapeText = value => String(value ?? "")
  .replace(/\\/g, "\\\\")
  .replace(/;/g, "\\;")
  .replace(/,/g, "\\,")
  .replace(/\r?\n/g, "\\n");

const calendarDate = value => String(value).replaceAll("-", "");
const nextDate = value => {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().slice(0, 10);
};
const stamp = value => value.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");

const eventLines = ({ placement, recipe, baseUrl, exportedAt }) => {
  const url = new URL(`recipes/${encodeURIComponent(recipe.slug)}/`, baseUrl).href;
  const title = `${placement.moment} — ${recipe.title || recipe.slug}`;
  const description = `Recette CookiGram — créneau : ${placement.moment}. Export snapshot du planning CookiGram.\n${url}`;
  const uid = `${recipe.slug}-${placement.date}-${placement.moment.toLowerCase()}@cookigram`;
  return [
    "BEGIN:VEVENT",
    `UID:${escapeText(uid)}`,
    `DTSTAMP:${stamp(exportedAt)}`,
    `DTSTART;VALUE=DATE:${calendarDate(placement.date)}`,
    `DTEND;VALUE=DATE:${calendarDate(nextDate(placement.date))}`,
    `SUMMARY:${escapeText(title)}`,
    `DESCRIPTION:${escapeText(description)}`,
    `URL:${escapeText(url)}`,
    "END:VEVENT",
  ];
};

export const buildCalendarExport = ({ placements, selection, weekDates, baseUrl, exportedAt = new Date() }) => {
  const dates = new Set(weekDates);
  const recipes = new Map(selection.map(recipe => [recipe.slug, recipe]));
  const visible = Object.values(placements || {})
    .filter(placement => dates.has(placement?.date))
    .sort((left, right) => `${left.date}|${MOMENTS.indexOf(left.moment)}`.localeCompare(`${right.date}|${MOMENTS.indexOf(right.moment)}`));
  const invalid = visible.filter(placement => !MOMENTS.includes(placement?.moment) || !recipes.has(placement?.slug));
  if (invalid.length) {
    throw new Error("Un ou plusieurs placements de cette semaine ne peuvent pas être exportés.");
  }

  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//CookiGram//Planner//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    ...visible.flatMap(placement => eventLines({ placement, recipe: recipes.get(placement.slug), baseUrl, exportedAt })),
    "END:VCALENDAR",
  ];
  return `${lines.join("\r\n")}\r\n`;
};

export const CALENDAR_MOMENTS = MOMENTS;
