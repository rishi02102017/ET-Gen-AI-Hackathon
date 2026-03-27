export type Stance = "supportive" | "neutral" | "critical";

export interface ArticleInputPayload {
  url?: string | null;
  text?: string | null;
  source_label?: string | null;
}

export interface AnalyzeRequestPayload {
  articles: ArticleInputPayload[];
}

export interface EvidenceSpan {
  quote: string;
  role: "stance_support" | "emphasis" | "tone" | "actor_framing";
}

export interface AtomicClaim {
  claim: string;
  support_quote: string | null;
}

export interface PerArticleFraming {
  article_index: number;
  source_label: string;
  stance: Stance;
  sentiment_score: number;
  emphasis_terms: string[];
  protagonist_descriptor: string | null;
  antagonist_descriptor: string | null;
  atomic_claims: AtomicClaim[];
  omission_candidates: string[];
  evidence: EvidenceSpan[];
  analysis_notes: string | null;
}

export interface EventHypothesis {
  title: string;
  neutral_summary: string;
  key_entities: string[];
}

export interface ResolvedArticle {
  index: number;
  source_label: string;
  url: string | null;
  excerpt: string;
  content_sha256: string;
  word_count: number;
}

export interface DivergenceBreakdown {
  stance_spread: number;
  emphasis_mismatch: number;
  coverage_asymmetry: number;
  actor_framing_delta: number;
  weights: Record<string, number>;
}

export interface DivergenceResult {
  score_0_100: number;
  band: "low" | "moderate" | "high";
  breakdown: DivergenceBreakdown;
  interpretation: string;
}

export interface AnalysisMeta {
  model_id: string;
  pipeline_version: string;
  warnings: string[];
  /** True when primary provider was configured but the successful completion used Groq backup. */
  llm_fallback_used?: boolean;
}

export interface AnalysisResponsePayload {
  event: EventHypothesis;
  articles: ResolvedArticle[];
  framing: PerArticleFraming[];
  divergence: DivergenceResult;
  meta: AnalysisMeta;
}
