import type { Category, Part, Specs } from "./types";

export const CATEGORY: Record<Category, { tab: string; label: string; color: string }> = {
  bearing: { tab: "BRG", label: "Bearing", color: "var(--color-tab-bearing)" },
  belt: { tab: "BLT", label: "V-belt", color: "var(--color-tab-belt)" },
  filter: { tab: "FLT", label: "Filter", color: "var(--color-tab-filter)" },
  motor: { tab: "MTR", label: "Motor", color: "var(--color-tab-motor)" },
};

type Column = { key: string; label: string; format?: (specs: Specs) => string | null };

const mm = (v: unknown) => (v == null ? null : `${v} mm`);

/** The spec columns a catalog page shows for each category. */
export const SPEC_COLUMNS: Record<Category, Column[]> = {
  bearing: [
    { key: "bore_mm", label: "Bore", format: (s) => mm(s.bore_mm) },
    { key: "outer_diameter_mm", label: "OD", format: (s) => mm(s.outer_diameter_mm) },
    { key: "width_mm", label: "Width", format: (s) => mm(s.width_mm) },
    { key: "sealing", label: "Sealing", format: (s) => String(s.sealing) },
  ],
  belt: [
    { key: "section", label: "Section", format: (s) => String(s.section) },
    { key: "length", label: "Length", format: (s) => `${s.length} ${s.length_unit === "in" ? "in" : "mm"}` },
    { key: "top_width_mm", label: "Top width", format: (s) => mm(s.top_width_mm) },
  ],
  filter: [
    { key: "kind", label: "Type", format: (s) => String(s.kind) },
    { key: "micron", label: "Rating", format: (s) => (s.micron != null ? `${s.micron} µm` : s.thread ? String(s.thread) : null) },
    { key: "length_mm", label: "Size", format: (s) =>
        s.length_mm != null ? `${s.length_mm} mm long`
        : s.outer_diameter_mm != null ? `Ø${s.outer_diameter_mm} × ${s.height_mm} mm`
        : s.height_mm != null ? `${s.height_mm} mm high` : null },
  ],
  motor: [
    { key: "power_kw", label: "Power", format: (s) => `${Number(s.power_kw)} kW` },
    { key: "poles", label: "Poles", format: (s) => `${s.poles}-pole` },
    { key: "frame", label: "Frame", format: (s) => `IEC ${s.frame}` },
    { key: "mounting", label: "Mount", format: (s) => (s.mounting === "B3" ? "Foot B3" : "Flange B5") },
  ],
};

export function specCells(part: Part): { key: string; label: string; value: string }[] {
  return SPEC_COLUMNS[part.category].map((c) => ({
    key: c.key,
    label: c.label,
    value: c.format ? c.format(part.specs) ?? "–" : String(part.specs[c.key] ?? "–"),
  }));
}

export function specLine(part: Part): string {
  return specCells(part).map((c) => c.value).join(" · ");
}

/** Spec columns whose values differ between the options: what the buyer didn't tell us. */
export function differingKeys(parts: Part[]): Set<string> {
  const keys = new Set<string>();
  if (parts.length < 2) return keys;
  const cells = parts.map(specCells);
  cells[0].forEach((cell, i) => {
    if (cells.some((row) => row[i]?.value !== cell.value)) keys.add(cell.key);
  });
  return keys;
}

export function money(value: string | number | null | undefined): string {
  if (value == null) return "–";
  return Number(value).toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function shortDate(iso: string | null): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
