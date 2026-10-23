"use client";

import { useState } from "react";
import { CircleCheck, LoaderCircle } from "lucide-react";
import { money, shortDate } from "@/lib/catalog";
import type { Rfq } from "@/lib/types";
import { Button } from "@/components/ui";

/** Quotes compared on one baseline: same columns, same units, cheapest first. */
export function QuotesTable({ rfq, waiting, onChange }: {
  rfq: Rfq; waiting: boolean; onChange: (path: string, init: RequestInit) => Promise<void>;
}) {
  const [accepting, setAccepting] = useState<string | null>(null);
  const awarded = rfq.status === "awarded";
  const lineCount = rfq.lines.length;

  async function accept(quoteId: string) {
    setAccepting(quoteId);
    await onChange(`/quotes/${quoteId}/accept`, { method: "POST" });
    setAccepting(null);
  }

  return (
    <section className="mt-12" aria-labelledby="quotes-heading">
      <div className="flex items-end justify-between border-b border-ink pb-2">
        <h2 id="quotes-heading" className="text-[1.0625rem] font-bold">Quotes</h2>
        <span className="text-ink-2">Prices come from each seller’s price list. The AI drafts, the seller approves.</span>
      </div>

      {waiting ? (
        <div className="flex items-center gap-2 py-8 text-ink-2" role="status">
          <LoaderCircle className="size-4 animate-spin text-catalog" aria-hidden />
          Waiting for quotes. Bot sellers usually answer within a minute; you can also switch to Seller and quote it yourself.
        </div>
      ) : (
        <table className="w-full text-left">
          <thead className="bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
            <tr>
              <th className="px-3 py-2">Seller</th>
              <th className="px-3 py-2 text-right">Parts</th>
              <th className="px-3 py-2 text-right">Shipping</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2 text-right">Lead time</th>
              <th className="px-3 py-2">Supplies</th>
              <th className="px-3 py-2">Received</th>
              <th className="px-3 py-2"><span className="sr-only">Action</span></th>
            </tr>
          </thead>
          <tbody>
            {rfq.quotes.map((q) => {
              const supplied = lineCount - q.lines_not_supplied;
              return (
                <tr key={q.id} className={`border-b border-rule ${q.status === "accepted" ? "bg-ok-tint" : ""}`}>
                  <td className="px-3 py-3 font-semibold">
                    {q.seller_name}
                    {q.is_your_shop && <span className="ml-2 text-label font-normal text-ink-2">your shop</span>}
                  </td>
                  <td className="figures px-3 py-3 text-right">{money(q.subtotal)}</td>
                  <td className="figures px-3 py-3 text-right text-ink-2">{money(q.shipping)}</td>
                  <td className="figures condensed px-3 py-3 text-right text-figure font-bold">{money(q.total)}</td>
                  <td className="figures px-3 py-3 text-right">{q.lead_time_days != null ? `${q.lead_time_days} days` : "–"}</td>
                  <td className={`px-3 py-3 ${supplied < lineCount ? "font-semibold text-choose" : ""}`}>
                    {supplied}/{lineCount} lines
                  </td>
                  <td className="figures px-3 py-3 text-ink-2">{shortDate(q.submitted_at)}</td>
                  <td className="px-3 py-3 text-right">
                    {q.status === "accepted" ? (
                      <span className="inline-flex items-center gap-1.5 font-semibold text-ok"><CircleCheck className="size-4" aria-hidden /> Accepted</span>
                    ) : q.status === "rejected" ? (
                      <span className="text-ink-3">Not chosen</span>
                    ) : !awarded ? (
                      <Button variant="primary" onClick={() => accept(q.id)} busy={accepting === q.id} disabled={!!accepting} className="h-8">
                        Accept
                      </Button>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
