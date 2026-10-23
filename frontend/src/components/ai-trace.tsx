import { Sparkles } from "lucide-react";
import type { AiSummary } from "@/lib/types";

const FEATURE_LABEL: Record<string, string> = {
  extraction: "extraction",
  matching: "matching",
  quoting: "quote drafting",
  search_query: "search",
};

/** What the AI did for this request: real numbers from the AI call log. */
export function AiTrace({ ai }: { ai: AiSummary | null }) {
  if (!ai) return null;
  const parts = Object.entries(ai.by_feature)
    .filter(([f]) => FEATURE_LABEL[f])
    .map(([f, n]) => `${n} ${FEATURE_LABEL[f]}`);
  return (
    <div className="figures flex items-center gap-2 text-ink-2" title={`${ai.tokens.toLocaleString()} tokens`}>
      <Sparkles className="size-4 text-catalog" aria-hidden />
      <span>
        <span className="font-semibold text-ink">{ai.model_calls} AI calls</span>
        {parts.length > 0 && <> ({parts.join(", ")})</>} · {(ai.model_time_ms / 1000).toFixed(1)} s model time ·{" "}
        <span className="font-semibold text-ink">${ai.cost_usd.toFixed(4)}</span>
      </span>
    </div>
  );
}
