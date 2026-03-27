import type { AnalysisResponsePayload, AnalyzeRequestPayload, HealthPayload } from "../types";

export async function fetchHealth(): Promise<HealthPayload | null> {
  try {
    const res = await fetch("/api/v1/health");
    if (!res.ok) return null;
    return (await res.json()) as HealthPayload;
  } catch {
    return null;
  }
}

export async function analyzeArticles(
  body: AnalyzeRequestPayload,
): Promise<AnalysisResponsePayload> {
  const res = await fetch("/api/v1/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as {
        detail?: string | Array<{ msg?: string }>;
      };
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = data.detail.map((d) => d.msg).filter(Boolean).join("; ") || detail;
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail || "Request failed");
  }
  return (await res.json()) as AnalysisResponsePayload;
}
