"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Send, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { differingKeys, shortDate, specCells } from "@/lib/catalog";
import type { Part, Rfq, RfqLine } from "@/lib/types";
import { Button, CategoryTab, Loading, Notice, PageTitle, PartCell, StatusMark } from "@/components/ui";
import { AiTrace } from "@/components/ai-trace";
import { QuotesTable } from "./quotes-table";

export function RequestView() {
  const { id } = useParams<{ id: string }>();
  const [rfq, setRfq] = useState<Rfq | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);

  const load = useCallback(() => api<Rfq>(`/rfqs/${id}`).then(setRfq).catch((e) => setError(e.message)), [id]);
  useEffect(() => { load(); }, [load]);

  // Quotes from bot sellers arrive in the background: check every few seconds while waiting.
  const waiting = rfq?.status === "published" && rfq.quotes.length === 0;
  useEffect(() => {
    if (!waiting) return;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [waiting, load]);

  async function change(path: string, init: RequestInit) {
    setError(null);
    try {
      setRfq(await api<Rfq>(path, init));
    } catch (e) {
      setError(e instanceof Error ? e.message : "That didn’t work. Try again.");
    }
  }

  async function publish() {
    setPublishing(true);
    await change(`/rfqs/${id}/publish`, { method: "POST" });
    setPublishing(false);
  }

  if (!rfq) return error ? <Notice>{error}</Notice> : <Loading />;

  const draft = rfq.status === "draft";
  const open = rfq.lines.filter((l) => !l.part).length;

  return (
    <>
      <Link href="/buyer" className="mb-3 inline-flex items-center gap-1.5 text-catalog hover:underline">
        <ArrowLeft className="size-4" aria-hidden /> My requests
      </Link>
      <PageTitle>{draft ? "Check the parts list" : rfq.status === "awarded" ? "Request · quote accepted" : "Request · open for quotes"}</PageTitle>

      <div className="mt-5 grid gap-6 md:grid-cols-[minmax(0,1fr)_260px]">
        <blockquote className="border-l border-rule-strong pl-4 whitespace-pre-line text-ink-2">{rfq.raw_text}</blockquote>
        <dl className="grid grid-cols-[auto_1fr] content-start gap-x-4 gap-y-1">
          <dt className="text-ink-2">Created</dt><dd className="figures">{shortDate(rfq.created_at)}</dd>
          <dt className="text-ink-2">Needed by</dt><dd>{rfq.needed_by ?? "Not stated"}</dd>
          {rfq.notes && (<><dt className="text-ink-2">Notes</dt><dd>{rfq.notes}</dd></>)}
        </dl>
      </div>

      {draft && (
        <p className="mt-6 max-w-[75ch] text-ink-2">
          The AI matched each line to the catalog. Check the matches, pick an option where it asks you to, and remove
          anything we don’t sell. Sellers only see the list after you publish.
        </p>
      )}

      {error && <div className="mt-4"><Notice>{error}</Notice></div>}

      <LinesTable rfq={rfq} draft={draft} onChange={change} />

      {!draft && <QuotesTable rfq={rfq} waiting={waiting} onChange={change} />}

      {draft && (
        <div className="sticky bottom-0 z-10 mt-8 border-t border-ink bg-paper/95 py-3 backdrop-blur-sm">
          <div className="flex flex-wrap items-center gap-4">
            <AiTrace ai={rfq.ai} />
            <div className="ml-auto flex items-center gap-4">
              <span className={open ? "font-semibold text-choose" : "text-ink-2"}>
                {open ? `${open} ${open === 1 ? "line needs" : "lines need"} a part` : "Every line has a part"}
              </span>
              <Button variant="primary" onClick={publish} disabled={open > 0 || rfq.lines.length === 0} busy={publishing} className="h-10 px-5">
                <Send className="size-4" aria-hidden /> Publish to sellers
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function LinesTable({ rfq, draft, onChange }: { rfq: Rfq; draft: boolean; onChange: (path: string, init: RequestInit) => Promise<void> }) {
  const base = `/rfqs/${rfq.id}/lines`;
  return (
    <table className="mt-6 w-full table-fixed text-left">
      <thead className="border-b border-ink bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
        <tr>
          <th className="w-10 p-0"><span className="sr-only">Category</span></th>
          <th className="w-20 px-3 py-2 text-right">Qty</th>
          <th className="w-[26%] px-3 py-2">You asked for</th>
          <th className="px-3 py-2">Catalog match</th>
          <th className="w-[27%] px-3 py-2">AI decision</th>
          {draft && <th className="w-10 px-2 py-2"><span className="sr-only">Remove</span></th>}
        </tr>
      </thead>
      {rfq.lines.map((line) => (
        <LineRows key={`${line.id}-${line.quantity}`} line={line} draft={draft}
          onPick={(part_id) => onChange(`${base}/${line.id}`, { method: "PATCH", body: JSON.stringify({ part_id }) })}
          onQty={(quantity) => onChange(`${base}/${line.id}`, { method: "PATCH", body: JSON.stringify({ quantity }) })}
          onRemove={() => onChange(`${base}/${line.id}`, { method: "DELETE" })}
        />
      ))}
      {rfq.lines.length === 0 && (
        <tbody><tr><td colSpan={6} className="px-3 py-8 text-center text-ink-2">No lines left. Start a new request instead.</td></tr></tbody>
      )}
    </table>
  );
}

function LineRows({ line, draft, onPick, onQty, onRemove }: {
  line: RfqLine; draft: boolean; onPick: (id: number) => void; onQty: (q: number) => void; onRemove: () => void;
}) {
  const [qty, setQty] = useState(String(line.quantity));
  const category = line.part?.category ?? line.suggestions[0]?.category ?? null;
  const chosenGroup = line.suggestions.find((s) => s.brand_options.some((o) => o.part_id === line.part?.part_id));
  const showOptions = line.match_status === "needs_choice" && line.suggestions.length > 0;

  function commitQty() {
    const n = Number(qty);
    if (Number.isInteger(n) && n >= 1 && n !== line.quantity) onQty(n);
    else setQty(String(line.quantity));
  }

  return (
    <tbody className="border-b border-rule">
      <tr key={line.part?.part_id ?? "none"} className={line.part && line.match_status === "needs_choice" ? "settle" : ""}>
        <td className="p-0 pt-3 align-top"><CategoryTab category={category} /></td>
        <td className="px-3 py-3 text-right align-top">
          {draft ? (
            <input
              aria-label={`Quantity for line ${line.line_no}`}
              inputMode="numeric" value={qty} onChange={(e) => setQty(e.target.value)} onBlur={commitQty}
              onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
              className="h-8 w-16 rounded-[3px] border border-rule-strong px-2 text-right hover:border-ink-2 focus:border-catalog focus:outline-none"
            />
          ) : (
            <span className="figures font-semibold">{line.quantity}</span>
          )}
        </td>
        <td className="px-3 py-3 align-top">
          <div>{line.description}</div>
          {(line.part_number_raw || line.brand_raw) && (
            <div className="mt-0.5 text-label text-ink-2">
              {line.part_number_raw && <>P/N <span className="font-semibold">{line.part_number_raw}</span></>}
              {line.part_number_raw && line.brand_raw && " · "}
              {line.brand_raw && <>Brand <span className="font-semibold">{line.brand_raw}</span></>}
            </div>
          )}
        </td>
        <td className="px-3 py-3 align-top">
          {line.part ? (
            <>
              <PartCell part={line.part} />
              {draft && chosenGroup && chosenGroup.brand_options.length > 1 && (
                <BrandSelect options={chosenGroup.brand_options} value={line.part.part_id} onChange={onPick} />
              )}
            </>
          ) : line.match_status === "needs_choice" ? (
            <span className="text-ink-2">Pick one of the options below</span>
          ) : (
            <span className="text-ink-2">We don’t carry this part</span>
          )}
        </td>
        <td className="px-3 py-3 align-top">
          <StatusMark status={line.match_status} chosen={!!line.part} />
          {line.match_reason && <p className="mt-1 text-ink-2">{line.match_reason}</p>}
        </td>
        {draft && (
          <td className="px-2 py-3 align-top">
            <button onClick={onRemove} className="rounded-[3px] p-1.5 text-ink-3 hover:bg-miss-tint hover:text-miss" aria-label={`Remove line ${line.line_no}`} title="Remove line">
              <Trash2 className="size-4" />
            </button>
          </td>
        )}
      </tr>
      {showOptions && (draft || !line.part) && (
        <tr>
          <td />
          <td colSpan={draft ? 5 : 4} className="px-3 pb-4">
            <Options line={line} draft={draft} onPick={onPick} />
          </td>
        </tr>
      )}
    </tbody>
  );
}

/** The options the agent offered, as catalog rows. Specs that differ between options are highlighted. */
function Options({ line, draft, onPick }: { line: RfqLine; draft: boolean; onPick: (id: number) => void }) {
  const parts: Part[] = line.suggestions;
  const differ = differingKeys(parts);
  const columns = specCells(parts[0]);
  const chosen = new Set(line.suggestions.filter((s) => s.brand_options.some((o) => o.part_id === line.part?.part_id)).map((s) => s.part_id));

  return (
    <div className="border border-choose/40 bg-choose-tint/40">
      <div className="px-3 pt-2 pb-1 text-label font-semibold uppercase tracking-wider text-choose">
        {parts.length} options · highlighted = what your request didn’t say
      </div>
      <table className="w-full text-left">
        <thead className="text-label text-ink-2">
          <tr>
            <th className="px-3 py-1 font-semibold">Part</th>
            {columns.map((c) => (
              <th key={c.key} className={`px-3 py-1 font-semibold ${differ.has(c.key) ? "text-choose" : ""}`}>{c.label}</th>
            ))}
            {draft && <th />}
          </tr>
        </thead>
        <tbody>
          {parts.map((p) => {
            const isChosen = chosen.has(p.part_id);
            return (
              <tr key={p.part_id} className={`border-t border-choose/20 ${isChosen ? "bg-paper" : ""}`}>
                <td className="px-3 py-2"><PartCell part={p} compact /></td>
                {specCells(p).map((c) => (
                  <td key={c.key} className={`figures px-3 py-2 ${differ.has(c.key) ? "font-bold text-ink" : "text-ink-2"}`}>
                    {differ.has(c.key) ? <mark className="rounded-[2px] bg-choose-tint px-1 text-ink">{c.value}</mark> : c.value}
                  </td>
                ))}
                {draft && (
                  <td className="px-3 py-2 text-right">
                    {isChosen ? (
                      <span className="font-semibold text-ok">Selected</span>
                    ) : (
                      <Button variant="secondary" onClick={() => onPick(p.part_id)} className="h-8">Use this</Button>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BrandSelect({ options, value, onChange }: { options: Part[]; value: number; onChange: (id: number) => void }) {
  return (
    <label className="mt-1.5 inline-flex items-center gap-2 text-label text-ink-2">
      Brand
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-7 rounded-[3px] border border-rule-strong bg-paper px-1.5 text-label font-semibold text-ink hover:border-ink-2 focus:border-catalog focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.part_id} value={o.part_id}>{o.brand} · {o.part_number}</option>
        ))}
      </select>
      <span>interchangeable</span>
    </label>
  );
}

