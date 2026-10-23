export type Category = "bearing" | "belt" | "filter" | "motor";
export type MatchStatus = "matched" | "needs_choice" | "not_found";
export type Specs = Record<string, string | number>;

export type Part = {
  part_id: number;
  brand: string;
  part_number: string;
  description: string;
  category: Category;
  specs: Specs;
};

export type Suggestion = Part & { brand_options: Part[] };

export type RfqLine = {
  id: string;
  line_no: number;
  part_number_raw: string | null;
  brand_raw: string | null;
  description: string;
  quantity: number;
  match_status: MatchStatus;
  match_reason: string | null;
  part: Part | null;
  suggestions: Suggestion[];
};

export type QuoteSummary = {
  id: string;
  seller_name: string;
  is_your_shop: boolean;
  status: "draft" | "submitted" | "accepted" | "rejected";
  subtotal: string | null;
  shipping: string | null;
  total: string | null;
  lead_time_days: number | null;
  notes: string | null;
  submitted_at: string | null;
  lines_not_supplied: number;
};

export type Rfq = {
  id: string;
  buyer_name: string;
  is_sample: boolean;
  raw_text: string;
  needed_by: string | null;
  notes: string | null;
  status: "draft" | "published" | "awarded";
  created_at: string;
  published_at: string | null;
  lines: RfqLine[];
  quotes: QuoteSummary[];
  ai: AiSummary | null;
};

export type RfqListItem = {
  id: string;
  raw_text: string;
  status: Rfq["status"];
  created_at: string;
  line_count: number;
  quote_count: number;
};

export type Me = { user_id: string; email: string; shop: { id: number; name: string } };

export type AiSummary = {
  model_calls: number;
  tokens: number;
  cost_usd: number;
  model_time_ms: number;
  by_feature: Record<string, number>;
};
