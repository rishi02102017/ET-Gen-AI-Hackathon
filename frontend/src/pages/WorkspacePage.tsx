import { useMemo, useState } from "react";
import "../App.css";
import { analyzeArticles } from "../api/client";
import { LoadingExperience } from "../components/LoadingExperience";
import { ResultsDashboard } from "../components/ResultsDashboard";
import type { AnalysisResponsePayload, ArticleInputPayload } from "../types";

type Row = ArticleInputPayload & { key: string };

function makeKey() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function emptyRow(): Row {
  return { key: makeKey(), url: "", text: "", source_label: "" };
}

export function WorkspacePage() {
  const [rows, setRows] = useState<Row[]>(() => [emptyRow(), emptyRow()]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponsePayload | null>(null);

  const canSubmit = useMemo(
    () =>
      rows.length >= 2 &&
      rows.every((r) => (r.url && r.url.trim()) || (r.text && r.text.trim())),
    [rows],
  );

  function updateRow(key: string, patch: Partial<ArticleInputPayload>) {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  }

  function addRow() {
    if (rows.length >= 6) return;
    setRows((prev) => [...prev, emptyRow()]);
  }

  function removeRow(key: string) {
    setRows((prev) => (prev.length <= 2 ? prev : prev.filter((r) => r.key !== key)));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const articles: ArticleInputPayload[] = rows.map((r) => {
        const url = r.url?.trim();
        const text = r.text?.trim();
        const source_label = r.source_label?.trim();
        const payload: ArticleInputPayload = {};
        if (url) payload.url = url;
        if (text) payload.text = text;
        if (source_label) payload.source_label = source_label;
        return payload;
      });
      const data = await analyzeArticles({ articles });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <main className="main">
        <section className="hero">
          <p className="hero-eyebrow">Multi-source news analysis</p>
          <h1 className="hero-title">
            See how each outlet <em>frames</em> the same story.
          </h1>
          <p className="hero-lead">
            Comparative stance, emphasis, and omission signals—fused into a transparent divergence
            index built for analysts, researchers, and editorial teams.
          </p>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-value">2–6</span>
              <span className="stat-label">Sources per run</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-value">4</span>
              <span className="stat-label">Subscore dimensions</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-value">100</span>
              <span className="stat-label">Point divergence scale</span>
            </div>
          </div>
        </section>

        {error ? (
          <div className="alert alert--error" role="alert">
            <span className="alert-icon" aria-hidden />
            <div>
              <strong>Request failed</strong>
              <p>{error}</p>
            </div>
          </div>
        ) : null}

        <section className="workspace" aria-labelledby="workspace-heading">
          <div className="workspace-head">
            <div>
              <h2 id="workspace-heading" className="workspace-title">
                Corpus
              </h2>
              <p className="workspace-desc">
                Add two to six articles via public URL, pasted full text, or both. When both are
                provided, pasted text takes precedence for analysis.
              </p>
            </div>
          </div>

          <form className="corpus-form" onSubmit={onSubmit}>
            <div className="article-stack">
              {rows.map((r, idx) => (
                <div key={r.key} className="article-card">
                  <div className="article-card-top">
                    <span className="article-index">Source {idx + 1}</span>
                    {rows.length > 2 ? (
                      <button
                        type="button"
                        className="btn-text"
                        onClick={() => removeRow(r.key)}
                        disabled={rows.length <= 2}
                      >
                        Remove
                      </button>
                    ) : null}
                  </div>
                  <div className="field-grid">
                    <label className="field">
                      <span className="field-label">Label</span>
                      <input
                        className="field-input"
                        value={r.source_label ?? ""}
                        onChange={(e) => updateRow(r.key, { source_label: e.target.value })}
                        placeholder={`Outlet ${idx + 1}`}
                        autoComplete="off"
                      />
                    </label>
                    <label className="field field--wide">
                      <span className="field-label">Article URL</span>
                      <input
                        className="field-input"
                        value={r.url ?? ""}
                        onChange={(e) => updateRow(r.key, { url: e.target.value })}
                        placeholder="https://"
                        inputMode="url"
                        autoComplete="url"
                      />
                    </label>
                    <label className="field field--full">
                      <span className="field-label">Pasted article text (optional)</span>
                      <textarea
                        className="field-input field-textarea"
                        value={r.text ?? ""}
                        onChange={(e) => updateRow(r.key, { text: e.target.value })}
                        placeholder="Full body text for paywalled pages or offline capture."
                        rows={5}
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn--ghost" onClick={addRow} disabled={rows.length >= 6}>
                Add source
              </button>
              <button type="submit" className="btn btn--primary" disabled={!canSubmit || loading}>
                <span className="btn-shine" aria-hidden />
                {loading ? "Running analysis…" : "Run comparative analysis"}
              </button>
            </div>
          </form>
        </section>

        {result ? <ResultsDashboard result={result} /> : null}
      </main>

      <LoadingExperience active={loading} />
    </>
  );
}
