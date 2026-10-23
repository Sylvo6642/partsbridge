"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { money, shortDate } from "@/lib/catalog";
import type { InboxItem } from "@/lib/types";
import { Loading, Notice, PageTitle } from "@/components/ui";

function QuoteState({ item }: { item: InboxItem }) {
  if (item.status === "awarded" && item.my_quote_status !== "accepted") return <span className="text-ink-3">Closed</span>;
  switch (item.my_quote_status) {
    case null: return <span className="font-semibold text-choose">Needs a quote</span>;
    case "draft": return <span className="font-semibold text-catalog">Draft · not sent</span>;
    case "submitted": return <span>Sent · waiting for buyer</span>;
    case "accepted": return <span className="font-semibold text-ok">Won</span>;
    case "rejected": return <span className="text-ink-3">Not chosen</span>;
  }
}

export default function InboxPage() {
  const [rows, setRows] = useState<InboxItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<InboxItem[]>("/seller/inbox").then(setRows).catch((e) => setError(e.message));
  }, []);

  return (
    <>
      <PageTitle>Inbox</PageTitle>
      <p className="mt-3 max-w-[75ch] text-ink-2">
        Requests from buyers. Open one and let the AI draft a quote from your stock and price list; nothing is sent until
        you submit it.
      </p>
      {error && <div className="mt-6"><Notice>{error}</Notice></div>}
      {!rows && !error && <Loading />}
      {rows && (
        <table className="mt-6 w-full table-fixed text-left">
          <thead className="border-b border-ink bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
            <tr>
              <th className="w-44 px-3 py-2">Buyer</th>
              <th className="px-3 py-2">Request</th>
              <th className="w-16 px-3 py-2 text-right">Lines</th>
              <th className="w-32 px-3 py-2">Needed by</th>
              <th className="w-48 px-3 py-2">Your quote</th>
              <th className="w-28 px-3 py-2 text-right">Total</th>
              <th className="w-32 px-3 py-2 text-right">Received</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-rule hover:bg-band-2">
                <td className="truncate px-3 py-3 font-semibold">{r.buyer_name === "You" ? "You (buyer side)" : r.buyer_name.replace(" (bot buyer)", "")}</td>
                <td className="max-w-0 px-3 py-3">
                  <Link href={`/seller/requests/${r.id}`} className="block truncate text-catalog hover:underline">{r.raw_text}</Link>
                </td>
                <td className="px-3 py-3 text-right">{r.line_count}</td>
                <td className="truncate px-3 py-3">{r.needed_by ?? <span className="text-ink-3">–</span>}</td>
                <td className="px-3 py-3 whitespace-nowrap"><QuoteState item={r} /></td>
                <td className="figures px-3 py-3 text-right">{r.my_quote_total != null ? money(r.my_quote_total) : "–"}</td>
                <td className="figures px-3 py-3 text-right whitespace-nowrap text-ink-2">{shortDate(r.published_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
