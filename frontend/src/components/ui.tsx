import { CircleAlert, CircleCheck, CircleHelp, CircleX, LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { CATEGORY, specLine } from "@/lib/catalog";
import type { Category, MatchStatus, Part } from "@/lib/types";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet" | "danger";
  busy?: boolean;
};

export function Button({ variant = "secondary", busy, className = "", children, disabled, ...rest }: ButtonProps) {
  const look = {
    primary: "bg-catalog text-white hover:bg-catalog-deep disabled:bg-ink-3",
    secondary: "bg-paper text-ink border border-rule-strong hover:border-ink-2 hover:bg-band-2 disabled:text-ink-3",
    quiet: "text-catalog hover:bg-catalog-tint disabled:text-ink-3",
    danger: "text-miss hover:bg-miss-tint disabled:text-ink-3",
  }[variant];
  return (
    <button
      className={`inline-flex h-9 items-center justify-center gap-2 rounded-[3px] px-3.5 text-body font-semibold whitespace-nowrap transition-colors duration-150 disabled:cursor-not-allowed ${look} ${className}`}
      disabled={disabled || busy}
      {...rest}
    >
      {busy && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

/** The catalog's edge tab: which section of the catalog a part comes from. */
export function CategoryTab({ category }: { category: Category | null }) {
  const c = category ? CATEGORY[category] : null;
  return (
    <span
      className="condensed inline-flex h-6 w-10 items-center justify-center rounded-r-[3px] text-label font-bold tracking-wider text-white"
      style={{ background: c?.color ?? "var(--color-rule-strong)" }}
      title={c?.label ?? "Not matched"}
    >
      {c?.tab ?? "—"}
    </span>
  );
}

const STATUS: Record<MatchStatus, { label: string; icon: typeof CircleCheck; className: string }> = {
  matched: { label: "Matched", icon: CircleCheck, className: "text-ok bg-ok-tint" },
  needs_choice: { label: "Choose one", icon: CircleHelp, className: "text-choose bg-choose-tint" },
  not_found: { label: "Not in catalog", icon: CircleX, className: "text-miss bg-miss-tint" },
};

export function StatusMark({ status, chosen }: { status: MatchStatus; chosen?: boolean }) {
  const s = status === "needs_choice" && chosen ? { ...STATUS.matched, label: "You chose" } : STATUS[status];
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-[3px] px-2 py-0.5 text-label font-semibold ${s.className}`}>
      <Icon className="size-3.5" aria-hidden />
      {s.label}
    </span>
  );
}

/** A part as a catalog entry: bold condensed part number, brand, then the spec line. */
export function PartCell({ part, compact }: { part: Part; compact?: boolean }) {
  return (
    <div className="min-w-0">
      <div className="flex items-baseline gap-2">
        <span className="condensed text-figure font-bold tracking-tight text-ink">{part.part_number}</span>
        <span className="text-label font-semibold uppercase tracking-wider text-ink-2">{part.brand}</span>
      </div>
      {!compact && <div className="figures truncate text-ink-2">{specLine(part)}</div>}
    </div>
  );
}

export function Notice({ tone = "error", children }: { tone?: "error" | "info"; children: ReactNode }) {
  const look = tone === "error" ? "bg-miss-tint text-miss" : "bg-catalog-tint text-catalog-deep";
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`flex items-start gap-2 rounded-[3px] px-3 py-2 ${look}`}>
      <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div>{children}</div>
    </div>
  );
}

export function PageTitle({ children, actions }: { children: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 border-b border-ink pb-3">
      <h1 className="text-title font-bold tracking-tight">{children}</h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-16 text-ink-2" role="status">
      <LoaderCircle className="size-4 animate-spin" aria-hidden /> {label}…
    </div>
  );
}
