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
  subtotal: string | number | null;
  shipping: string | number | null;
  total: string | number | null;
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

export type InboxItem = {
  id: string;
  buyer_name: string;
  is_sample: boolean;
  raw_text: string;
  needed_by: string | null;
  status: Rfq["status"];
  published_at: string | null;
  line_count: number;
  my_quote_status: QuoteSummary["status"] | null;
  my_quote_total: string | number | null;
};

export type QuoteLine = {
  id: string;
  rfq_line_id: string;
  part: Part | null;
  quantity: number;
  unit_price: string | number | null;
  line_total: string | number | null;
  lead_time_days: number | null;
  note: string | null;
  stock_qty: number | null;
};

export type MyQuote = {
  id: string;
  status: QuoteSummary["status"];
  subtotal: string | number | null;
  shipping: string | number | null;
  total: string | number | null;
  lead_time_days: number | null;
  notes: string | null;
  submitted_at: string | null;
  ai: AiSummary | null;
  lines: QuoteLine[];
};

export type SellerRfq = Rfq & { my_quote: MyQuote | null };
