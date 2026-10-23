"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Check, LoaderCircle, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { Rfq } from "@/lib/types";
import { Button, Notice, PageTitle } from "@/components/ui";

const EXAMPLES = [
  {
    label: "Maintenance email",
    text: "Hi team,\n\nPlease quote the following for our plant:\n- 6205DDU x 20\n- A42 V-belt, qty 8\n- Spin-on oil filter SO-UNF34-100, 6 nos\n\nNeed delivery within 2 weeks.\n\nRegards,\nRavi",
  },
  {
    label: "Descriptions, no part numbers",
    text: "We need two 1.5 kW 4 pole motors, foot mounted, plus a hydraulic return filter element 10 micron 400mm long (5 pcs) and 4 sealed bearings 40 x 90 x 23 mm.",
  },
  {
    label: "Vague on purpose",
    text: "Urgent: sealed bearing for a 25mm shaft x4, a 2.2 kW motor, and 6 SPZ wedge belts 1000mm.",
  },
];

const STEPS = [
  { label: "Reading your request", detail: "Structured extraction: part numbers, brands, quantities" },
  { label: "Matching each line to the catalog", detail: "One agent per line: search, spec filter, then a decision" },
  { label: "Preparing your review", detail: "Nothing goes to sellers until you publish" },
];

export default function NewRequestPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [step, setStep] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => () => clearTimeout(timer.current), []);

  async function analyze() {
    setError(null);
    setStep(0);
    // The API does all three steps in one call; extraction usually takes ~2 s, so move the marker on then.
    timer.current = setTimeout(() => setStep(1), 2200);
    try {
      const rfq = await api<Rfq>("/rfqs/analyze", { method: "POST", body: JSON.stringify({ text }) });
      clearTimeout(timer.current);
      setStep(2);
      router.push(`/buyer/requests/${rfq.id}`);
    } catch (e) {
      clearTimeout(timer.current);
      setStep(null);
      setError(e instanceof Error ? e.message : "The AI step failed. Try again.");
    }
  }

  const busy = step !== null;

  return (
    <>
      <PageTitle>New request</PageTitle>
      <div className="mt-6 grid gap-10 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section>
          <label htmlFor="request" className="mb-2 block font-semibold">
            Paste your request the way you’d write it in an email
          </label>
          <textarea
            id="request"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={busy}
            rows={12}
            maxLength={4000}
            placeholder={"e.g. Need 10x 6205 sealed bearings and 4 belts A42 for the conveyor,\nplus one 1.5 kW 4 pole motor, foot mount. Urgent."}
            className="figures w-full resize-y rounded-[3px] border border-rule-strong bg-paper px-3.5 py-3 text-[0.9375rem] leading-6 hover:border-ink-2 focus:border-catalog focus:outline-none disabled:bg-band-2 disabled:text-ink-2"
          />
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
            <span className="text-label font-semibold uppercase tracking-wider text-ink-2">Try an example</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setText(ex.text)}
                disabled={busy}
                className="text-catalog underline decoration-catalog/40 hover:decoration-catalog disabled:text-ink-3"
              >
                {ex.label}
              </button>
            ))}
          </div>

          {error && <div className="mt-4"><Notice>{error}</Notice></div>}

          <div className="mt-6 flex items-center gap-4">
            <Button variant="primary" onClick={analyze} disabled={text.trim().length < 3} busy={busy} className="h-10 px-5">
              {!busy && <Sparkles className="size-4" aria-hidden />}
              Analyze with AI
            </Button>
            <span className="text-ink-2">Takes 5–15 seconds. Costs about a fifth of a cent.</span>
          </div>
        </section>

        <aside aria-label="What happens next" aria-live="polite">
          <h2 className="border-b border-rule pb-2 text-label font-semibold uppercase tracking-wider text-ink-2">
            What happens next
          </h2>
          <ol className="mt-1">
            {STEPS.map((s, i) => {
              const state = step === null ? "idle" : i < step ? "done" : i === step ? "active" : "waiting";
              return (
                <li key={s.label} className="relative border-b border-rule py-3 pl-8">
                  <span className="absolute top-3.5 left-0 flex size-5 items-center justify-center">
                    {state === "done" ? <Check className="size-4 text-ok" aria-hidden />
                      : state === "active" ? <LoaderCircle className="size-4 animate-spin text-catalog" aria-hidden />
                      : <span className="figures text-label font-bold text-ink-3">{i + 1}</span>}
                  </span>
                  <div className={`font-semibold ${state === "active" ? "text-catalog" : state === "waiting" ? "text-ink-3" : ""}`}>
                    {s.label}
                  </div>
                  <div className="text-ink-2">{s.detail}</div>
                </li>
              );
            })}
          </ol>
        </aside>
      </div>
    </>
  );
}
