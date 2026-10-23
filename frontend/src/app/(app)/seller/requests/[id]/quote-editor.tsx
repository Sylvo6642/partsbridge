"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, CircleCheck, RotateCcw, Send, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { money, shortDate } from "@/lib/catalog";
import type { QuoteLine, RfqLine, SellerRfq } from "@/lib/types";
import { Button, CategoryTab, Loading, Notice, PageTitle, PartCell } from "@/components/ui";
import { AiTrace } from "@/components/ai-trace";

export function QuoteEditor() {
  const { id } = useParams<{ id: string }>();
  const [rfq, setRfq] = useState<SellerRfq | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"draft" | "submit" | "save" | null>(null);

  const load = useCallback(() => api<SellerRfq>(`/seller/rfqs/${id}`).then(setRfq).catch((e) => setError(e.message)), [id]);
  useEffect(() => { load(); }, [load]);

  async function run(kind: "draft" | "submit" | "save", path: string, init: RequestInit) {
    setBusy(kind);
    setError(null);
    try {
      setRfq(await api<SellerRfq>(path, init));
    } catch (e) {
      setError(e instanceof Error ? e.message : "That didn’t work. Try again.");
    }
    setBusy(null);
  }

  if (!rfq) return error ? <Notice>{error}</Notice> : <Loading />;

  const quote = rfq.my_quote;
  const editable = quote?.status === "draft";
  const open = rfq.status === "published";
  const draft = () => run("draft", `/seller/rfqs/${id}/draft`, { method: "POST" });

  return (
    <>
      <Link href="/seller" className="mb-3 inline-flex items-center gap-1.5 text-catalog hover:underline">
        <ArrowLeft className="size-4" aria-hidden /> Inbox
      </Link>
      <PageTitle>Quote for {rfq.buyer_name === "You" ? "your own request" : rfq.buyer_name.replace(" (bot buyer)", "")}</PageTitle>

      <div className="mt-5 grid gap-6 md:grid-cols-[minmax(0,1fr)_260px]">
        <blockquote className="border-l border-rule-strong pl-4 whitespace-pre-line text-ink-2">{rfq.raw_text}</blockquote>
        <dl className="grid grid-cols-[auto_1fr] content-start gap-x-4 gap-y-1">
          <dt className="text-ink-2">Received</dt><dd className="figures">{shortDate(rfq.published_at)}</dd>
          <dt className="text-ink-2">Needed by</dt><dd>{rfq.needed_by ?? "Not stated"}</dd>
          <dt className="text-ink-2">Your quote</dt>
          <dd className={quote?.status === "accepted" ? "font-semibold text-ok" : ""}>
            {!quote ? "Not started" : quote.status === "draft" ? "Draft · not sent" : quote.status === "submitted" ? "Sent" : quote.status === "accepted" ? "Won" : "Not chosen"}
          </dd>
        </dl>
      </div>

      {error && <div className="mt-4"><Notice>{error}</Notice></div>}

      {!quote ? (
        <>
          <RequestedLines lines={rfq.lines} />
          {open && (
            <div className="mt-8 flex flex-wrap items-center gap-4 border-t border-ink pt-4">
              <Button variant="primary" onClick={draft} busy={busy === "draft"} className="h-10 px-5">
                {busy !== "draft" && <Sparkles className="size-4" aria-hidden />} Draft quote with AI
              </Button>
              <p className="max-w-[70ch] text-ink-2">
                Reads the buyer’s notes, checks your stock and price list, and offers an equivalent brand when allowed.
                Prices come from your price list, never from the AI. You review before anything is sent.
              </p>
            </div>
          )}
        </>
      ) : (
        <QuoteTable
          rfq={rfq}
          editable={editable}
          saving={busy === "save"}
          onSave={(lines) => run("save", `/quotes/${quote.id}`, { method: "PUT", body: JSON.stringify({ lines }) })}
        />
      )}

      {quote && (
        <div className={`${editable ? "sticky bottom-0 z-10" : ""} mt-8 border-t border-ink bg-paper/95 py-3 backdrop-blur-sm`}>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
            <div className="min-w-0">
              {quote.notes && <p className="font-semibold">{quote.notes}</p>}
              <AiTrace ai={quote.ai} />
            </div>
            <dl className="figures ml-auto grid grid-cols-[auto_auto] gap-x-4 text-right">
              <dt className="text-ink-2">Parts</dt><dd>{money(quote.subtotal)}</dd>
              <dt className="text-ink-2">Shipping</dt><dd>{money(quote.shipping)}</dd>
              <dt className="font-semibold">Total</dt><dd className="condensed text-figure font-bold">{money(quote.total)}</dd>
            </dl>
            {editable ? (
              <div className="flex items-center gap-2">
                <Button variant="secondary" onClick={draft} busy={busy === "draft"} disabled={!!busy}>
                  {busy !== "draft" && <RotateCcw className="size-4" aria-hidden />} Redraft
                </Button>
                <Button variant="primary" onClick={() => run("submit", `/quotes/${quote.id}/submit`, { method: "POST" })}
                  busy={busy === "submit"} disabled={!!busy} className="h-10 px-5">
                  {busy !== "submit" && <Send className="size-4" aria-hidden />} Submit quote
                </Button>
              </div>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-semibold text-ok">
                <CircleCheck className="size-4" aria-hidden />
                {quote.status === "accepted" ? "The buyer accepted this quote" : quote.status === "rejected" ? "The buyer chose another quote" : `Sent ${shortDate(quote.submitted_at)}`}
              </span>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function RequestedLines({ lines }: { lines: RfqLine[] }) {
  return (
    <table className="mt-6 w-full table-fixed text-left">
      <thead className="border-b border-ink bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
        <tr>
          <th className="w-10 p-0"><span className="sr-only">Category</span></th>
          <th className="w-20 px-3 py-2 text-right">Qty</th>
          <th className="px-3 py-2">Requested part</th>
          <th className="w-[38%] px-3 py-2">Buyer’s words</th>
        </tr>
      </thead>
      <tbody>
        {lines.map((l) => (
          <tr key={l.id} className="border-b border-rule">
            <td className="p-0 pt-3 align-top"><CategoryTab category={l.part?.category ?? null} /></td>
            <td className="figures px-3 py-3 text-right align-top font-semibold">{l.quantity}</td>
            <td className="px-3 py-3 align-top">{l.part ? <PartCell part={l.part} /> : "–"}</td>
            <td className="px-3 py-3 align-top text-ink-2">{l.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type Edit = { id: string; quantity: number; unit_price: string | null };

function QuoteTable({ rfq, editable, saving, onSave }: {
  rfq: SellerRfq; editable: boolean; saving: boolean; onSave: (lines: Edit[]) => void;
}) {
  const byLine = new Map(rfq.my_quote!.lines.map((q) => [q.rfq_line_id, q]));
  return (
    <table className={`mt-6 w-full table-fixed text-left ${saving ? "opacity-70" : ""}`} aria-busy={saving}>
      <thead className="border-b border-ink bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
        <tr>
          <th className="w-10 p-0"><span className="sr-only">Category</span></th>
          <th className="w-[21%] px-3 py-2">Requested</th>
          <th className="px-3 py-2">You offer</th>
          <th className="w-20 px-3 py-2 text-right">Stock</th>
          <th className="w-24 px-3 py-2 text-right">Qty</th>
          <th className="w-28 px-3 py-2 text-right">Unit price</th>
          <th className="w-28 px-3 py-2 text-right">Line total</th>
          <th className="w-20 px-3 py-2 text-right">Lead</th>
        </tr>
      </thead>
      <tbody>
        {rfq.lines.map((line) => {
          const q = byLine.get(line.id);
          return q ? <QuoteRow key={`${q.id}-${q.quantity}-${q.unit_price}`} line={line} q={q} editable={editable} onSave={onSave} /> : null;
        })}
      </tbody>
    </table>
  );
}

function QuoteRow({ line, q, editable, onSave }: { line: RfqLine; q: QuoteLine; editable: boolean; onSave: (lines: Edit[]) => void }) {
  const [qty, setQty] = useState(String(q.quantity));
  const [price, setPrice] = useState(q.unit_price != null ? Number(q.unit_price).toFixed(2) : "");
  const substitute = q.part && line.part && q.part.part_id !== line.part.part_id;
  const short = q.part && q.stock_qty != null && q.stock_qty < q.quantity;

  function commit() {
    const n = Number(qty);
    const p = Number(price);
    const changed = n !== q.quantity || (q.unit_price != null && p.toFixed(2) !== Number(q.unit_price).toFixed(2));
    if (!Number.isInteger(n) || n < 0 || (q.part && !(p > 0))) {
      setQty(String(q.quantity));
      setPrice(q.unit_price != null ? Number(q.unit_price).toFixed(2) : "");
      return;
    }
    if (changed) onSave([{ id: q.id, quantity: n, unit_price: q.part ? p.toFixed(2) : null }]);
  }

  const input = "h-8 w-full rounded-[3px] border border-rule-strong px-2 text-right hover:border-ink-2 focus:border-catalog focus:outline-none";
  return (
    <tr className="border-b border-rule align-top">
      <td className="p-0 pt-3"><CategoryTab category={line.part?.category ?? null} /></td>
      <td className="px-3 py-3">
        {line.part && <PartCell part={line.part} compact />}
        <div className="text-label text-ink-2">{line.quantity} requested</div>
      </td>
      <td className="px-3 py-3">
        {q.part ? <PartCell part={q.part} compact /> : <span className="font-semibold text-miss">Can’t supply</span>}
        {q.note && <p className={`mt-0.5 ${substitute ? "text-choose" : "text-ink-2"}`}>{q.note}</p>}
      </td>
      <td className={`figures px-3 py-3 text-right ${short ? "font-semibold text-choose" : ""}`}>{q.stock_qty ?? "–"}</td>
      <td className="px-3 py-2.5 text-right">
        {editable && q.part ? (
          <input aria-label="Quantity" inputMode="numeric" value={qty} onChange={(e) => setQty(e.target.value)} onBlur={commit}
            onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()} className={input} />
        ) : <span className="figures">{q.part ? q.quantity : "–"}</span>}
      </td>
      <td className="px-3 py-2.5 text-right">
        {editable && q.part ? (
          <input aria-label="Unit price in USD" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} onBlur={commit}
            onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()} className={input} />
        ) : <span className="figures">{money(q.unit_price)}</span>}
      </td>
      <td className="figures px-3 py-3 text-right font-semibold">{money(q.line_total)}</td>
      <td className={`figures px-3 py-3 text-right ${q.lead_time_days != null && q.lead_time_days >= 10 ? "text-choose" : ""}`}>
        {q.lead_time_days != null ? `${q.lead_time_days} d` : "–"}
      </td>
    </tr>
  );
}
