"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { shortDate } from "@/lib/catalog";
import type { RfqListItem } from "@/lib/types";
import { Loading, Notice, PageTitle } from "@/components/ui";

const STATUS_LABEL: Record<RfqListItem["status"], string> = {
  draft: "Draft · needs review",
  published: "Open for quotes",
  awarded: "Quote accepted",
};

export default function MyRequestsPage() {
  const [rows, setRows] = useState<RfqListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<RfqListItem[]>("/rfqs").then(setRows).catch((e) => setError(e.message));
  }, []);

  return (
    <>
      <PageTitle
        actions={
          <Link href="/buyer/new" className="inline-flex h-9 items-center gap-2 rounded-[3px] bg-catalog px-3.5 font-semibold text-white hover:bg-catalog-deep">
            <Plus className="size-4" aria-hidden /> New request
          </Link>
        }
      >
        My requests
      </PageTitle>

      {error && <div className="mt-6"><Notice>{error}</Notice></div>}
      {!rows && !error && <Loading />}

      {rows?.length === 0 && (
        <div className="mt-10 max-w-[56ch]">
          <h2 className="text-[1rem] font-bold">No requests yet</h2>
          <p className="mt-1 text-ink-2">
            Paste a parts request the way you’d write it in an email. The AI turns it into a catalog-matched list you can
            check before sellers see it.
          </p>
          <Link href="/buyer/new" className="mt-4 inline-flex h-9 items-center gap-2 rounded-[3px] bg-catalog px-3.5 font-semibold text-white hover:bg-catalog-deep">
            <Plus className="size-4" aria-hidden /> Write your first request
          </Link>
        </div>
      )}

      {rows && rows.length > 0 && (
        <table className="mt-6 w-full text-left">
          <thead className="border-b border-ink bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
            <tr>
              <th className="px-3 py-2">Request</th>
              <th className="px-3 py-2 text-right">Lines</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2 text-right">Quotes</th>
              <th className="px-3 py-2 text-right">Created</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-rule hover:bg-band-2">
                <td className="max-w-0 px-3 py-3">
                  <Link href={`/buyer/requests/${r.id}`} className="block truncate font-semibold text-catalog hover:underline">
                    {r.raw_text}
                  </Link>
                </td>
                <td className="px-3 py-3 text-right">{r.line_count}</td>
                <td className="px-3 py-3 whitespace-nowrap">
                  <span className={r.status === "draft" ? "font-semibold text-choose" : r.status === "awarded" ? "font-semibold text-ok" : ""}>
                    {STATUS_LABEL[r.status]}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">{r.status === "draft" ? "–" : r.quote_count}</td>
                <td className="px-3 py-3 text-right whitespace-nowrap text-ink-2">{shortDate(r.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
