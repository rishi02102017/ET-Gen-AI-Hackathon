import type { AnalysisMeta } from "../types";

/**
 * Single human-readable line for judges; verbose warnings stay in the collapsible technical log.
 */
export function buildRunSummary(meta: AnalysisMeta): string | null {
  const hasWarnings = meta.warnings.length > 0;
  if (!hasWarnings && !meta.llm_fallback_used) return null;

  const blob = meta.warnings.join(" ");
  const rateLimited = /RateLimitError|rate limit|Rate limited/i.test(blob);
  const mock = /mock mode|deterministic mock|mock-deterministic/i.test(blob);
  const grounding = /Evidence and claim support quotes were checked/i.test(blob);
  const injected = /verbatim evidence excerpts auto-selected/i.test(blob);

  if (meta.llm_fallback_used && rateLimited) {
    return "Primary provider was rate-limited; this briefing finished on the backup model. Open Technical log below for retry details.";
  }
  if (meta.llm_fallback_used) {
    return "Primary request did not complete; this briefing used the backup model. See Technical log for details.";
  }
  if (mock) {
    return "Mock inference mode—add API keys for live structured analysis. See Technical log.";
  }
  if (grounding || injected) {
    return "Quotes were checked against source text (some removed or auto-filled). See analyst notes per source and Technical log.";
  }
  if (hasWarnings) {
    return "There are ingestion or model notices—expand Technical log for the full list.";
  }
  return null;
}
