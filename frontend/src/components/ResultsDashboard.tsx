import { useId } from "react";
import type { AnalysisResponsePayload, PerArticleFraming } from "../types";
import { buildRunSummary } from "../utils/runSummary";

type Props = { result: AnalysisResponsePayload };

const NAV_LINKS = [
  { id: "nav-event", label: "1 · Event" },
  { id: "nav-divergence", label: "2 · Divergence" },
  { id: "nav-drivers", label: "3 · Drivers" },
  { id: "nav-sources", label: "4 · Sources" },
  { id: "nav-audit", label: "5 · Audit" },
] as const;

export function ResultsDashboard({ result }: Props) {
  const d = result.divergence;
  const gradId = useId().replace(/:/g, "");
  const runSummary = buildRunSummary(result.meta);
  const warnCount = result.meta.warnings.length;

  return (
    <section className="results-section navigator">
      <div className="section-heading">
        <span className="section-eyebrow">News navigator</span>
        <h2 className="section-title">Interactive briefing</h2>
        <p className="section-lede navigator-lede">
          Explorable cross-source view: shared event hypothesis, how strongly narratives diverge, what
          drives the score, then per-outlet framing and audit metadata—aligned with intelligence-style news
          experiences.
        </p>
      </div>

      {runSummary ? (
        <div className="run-summary-banner" role="status">
          <span className="run-summary-label">Run summary</span>
          <p className="run-summary-text">{runSummary}</p>
        </div>
      ) : null}

      <nav className="navigator-toc" aria-label="Briefing sections">
        {NAV_LINKS.map(({ id, label }) => (
          <a key={id} className="navigator-toc__link" href={`#${id}`}>
            {label}
          </a>
        ))}
      </nav>

      <div id="nav-event" className="navigator-anchor" aria-hidden />

      <div className="navigator-panel">
        <div className="navigator-panel__head">
          <span className="navigator-step">Step 1</span>
          <h3 className="navigator-panel__title">Shared event hypothesis</h3>
          <p className="navigator-panel__blurb">
            One neutral synthesis the model treats as the common referent for comparing framing—not a claim
            of ground truth.
          </p>
        </div>
        <div className="card card--event navigator-card--full">
          <div className="card-kicker">Event</div>
          <h3 className="event-title">{result.event.title}</h3>
          <p className="event-summary">{result.event.neutral_summary}</p>
          <div className="entity-row">
            {result.event.key_entities.map((e) => (
              <span key={e} className="chip chip--entity">
                {e}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div id="nav-divergence" className="navigator-anchor" aria-hidden />

      <div className="navigator-panel">
        <div className="navigator-panel__head">
          <span className="navigator-step">Step 2</span>
          <h3 className="navigator-panel__title">Framing distance</h3>
          <p className="navigator-panel__blurb">
            A transparent 0–100 index from stance, emphasis, coverage/omission spread, and actor descriptors—
            fused with fixed weights on the server.
          </p>
        </div>
        <div className="bento bento--navigator">
          <div className="card card--divergence">
            <div className="card-kicker">Divergence index</div>
            <div className="divergence-visual">
              <DivergenceRing score={d.score_0_100} gradientId={gradId} />
              <div className="divergence-meta">
                <span className={`band-pill band-pill--${d.band}`}>{d.band} divergence</span>
                <p className="divergence-blurb">{d.interpretation}</p>
              </div>
            </div>
          </div>
          <div className="card card--compare-strip">
            <div className="card-kicker">At a glance</div>
            <div className="compare-strip-grid">
              {result.framing.map((f) => (
                <div key={f.article_index} className="compare-strip-cell">
                  <span className="compare-strip-label">{f.source_label}</span>
                  <span
                    className={`stance-badge stance-badge--compact ${
                      f.stance === "supportive"
                        ? "stance--support"
                        : f.stance === "critical"
                          ? "stance--critical"
                          : "stance--neutral"
                    }`}
                  >
                    {f.stance}
                  </span>
                  <span className="compare-strip-sent mono">{f.sentiment_score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div id="nav-drivers" className="navigator-anchor" aria-hidden />

      <div className="navigator-panel">
        <div className="navigator-panel__head">
          <span className="navigator-step">Step 3</span>
          <h3 className="navigator-panel__title">What drives the score</h3>
          <p className="navigator-panel__blurb">
            Decomposition into interpretable sub-signals (each 0–100%, weighted). Hover labels for short
            definitions.
          </p>
        </div>
        <div className="card card--subscores">
          <div className="card-kicker">Signal decomposition</div>
          <div className="subscore-grid">
            <SubScoreBar
              label="Stance spread"
              value={d.breakdown.stance_spread}
              weight={d.breakdown.weights.stance_spread}
            />
            <SubScoreBar
              label="Emphasis mismatch"
              value={d.breakdown.emphasis_mismatch}
              weight={d.breakdown.weights.emphasis_mismatch}
            />
            <SubScoreBar
              label="Coverage & omission spread"
              value={d.breakdown.coverage_asymmetry}
              weight={d.breakdown.weights.coverage_asymmetry}
              hint="Balance of extracted claims across sources plus how differently omission candidates diverge."
            />
            <SubScoreBar
              label="Actor framing delta"
              value={d.breakdown.actor_framing_delta}
              weight={d.breakdown.weights.actor_framing_delta}
            />
          </div>
        </div>
      </div>

      <div id="nav-sources" className="navigator-anchor" aria-hidden />

      <div className="navigator-panel">
        <div className="navigator-panel__head">
          <span className="navigator-step">Step 4</span>
          <h3 className="navigator-panel__title">Per-outlet framing & omissions</h3>
          <p className="navigator-panel__blurb">
            Stance, emphasis, omission signals, and verbatim-grounded quotes where available—compare how each
            source emphasizes or leaves out themes.
          </p>
        </div>
        <div className="framing-grid">
          {result.framing.map((f) => (
            <FramingCard key={f.article_index} f={f} />
          ))}
        </div>
      </div>

      <div id="nav-audit" className="navigator-anchor" aria-hidden />

      <div className="navigator-panel">
        <div className="navigator-panel__head">
          <span className="navigator-step">Step 5</span>
          <h3 className="navigator-panel__title">Audit trail</h3>
          <p className="navigator-panel__blurb">
            Model, pipeline version, content fingerprints, and an optional technical log for judges and
            engineers.
          </p>
        </div>
        <div className="card card--provenance">
          <div className="card-kicker">Provenance</div>
          <div className="prov-row">
            <div>
              <span className="prov-label">Model</span>
              <span className="prov-value prov-value--with-badge">
                {result.meta.model_id}
                {result.meta.llm_fallback_used ? (
                  <span
                    className="fallback-badge"
                    title="Primary endpoint failed or rate-limited; backup model produced this run."
                  >
                    Backup model
                  </span>
                ) : null}
              </span>
            </div>
            <div>
              <span className="prov-label">Pipeline</span>
              <span className="prov-value mono">{result.meta.pipeline_version}</span>
            </div>
          </div>

          {warnCount > 0 ? (
            <details className="prov-warn-details">
              <summary>
                Technical log
                <span className="prov-warn-count">{warnCount}</span>
              </summary>
              <p className="prov-warn-hint">
                Retries, rate limits, JSON mode fallbacks, and ingestion notices. Safe to ignore for a quick
                read—useful for reproducibility and debugging.
              </p>
              <ul className="warn-list">
                {result.meta.warnings.map((w, i) => (
                  <li key={`${i}-${w.slice(0, 48)}`}>{w}</li>
                ))}
              </ul>
            </details>
          ) : null}

          <div className="prov-table-wrap">
            <table className="prov-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Words</th>
                  <th>Content fingerprint</th>
                </tr>
              </thead>
              <tbody>
                {result.articles.map((a) => (
                  <tr key={a.index}>
                    <td>
                      {a.url ? (
                        <a href={a.url} target="_blank" rel="noreferrer" className="prov-link">
                          {a.source_label}
                        </a>
                      ) : (
                        a.source_label
                      )}
                    </td>
                    <td>{a.word_count.toLocaleString()}</td>
                    <td className="mono muted-fg">{a.content_sha256.slice(0, 20)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

function DivergenceRing({ score, gradientId }: { score: number; gradientId: string }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, score)) / 100) * c;

  return (
    <div className="ring-wrap">
      <svg className="ring-svg" viewBox="0 0 120 120" aria-hidden>
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#5eead4" />
            <stop offset="50%" stopColor="#d4a574" />
            <stop offset="100%" stopColor="#fb7185" />
          </linearGradient>
        </defs>
        <circle className="ring-track" cx="60" cy="60" r={r} />
        <circle
          className="ring-progress"
          cx="60"
          cy="60"
          r={r}
          stroke={`url(#${gradientId})`}
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
        />
      </svg>
      <div className="ring-center">
        <span className="ring-score">{score}</span>
        <span className="ring-unit">/ 100</span>
      </div>
    </div>
  );
}

function SubScoreBar(props: { label: string; value: number; weight: number; hint?: string }) {
  const pct = Math.round(props.value * 100);
  return (
    <div className="subscore-item">
      <div className="subscore-head">
        <span className="subscore-label" title={props.hint}>
          {props.label}
        </span>
        <span className="subscore-meta">
          <span className="subscore-pct">{pct}%</span>
          <span className="subscore-w">w {props.weight.toFixed(2)}</span>
        </span>
      </div>
      <div className="subscore-track">
        <div className="subscore-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function FramingCard({ f }: { f: PerArticleFraming }) {
  const stanceClass =
    f.stance === "supportive" ? "stance--support" : f.stance === "critical" ? "stance--critical" : "stance--neutral";
  const sentPct = ((f.sentiment_score + 1) / 2) * 100;
  const actors =
    [f.protagonist_descriptor, f.antagonist_descriptor].filter(Boolean).join(" · ") || null;

  return (
    <article className="framing-card">
      <header className="framing-card-head">
        <div>
          <h4 className="framing-source">{f.source_label}</h4>
          <span className={`stance-badge ${stanceClass}`}>{f.stance}</span>
        </div>
        <div className="sentiment-meter" title={`Sentiment ${f.sentiment_score.toFixed(2)}`}>
          <span className="sentiment-label">Polarity</span>
          <div className="sentiment-track">
            <div className="sentiment-mid" />
            <div className="sentiment-fill" style={{ width: `${sentPct}%` }} />
          </div>
          <span className="sentiment-val">{f.sentiment_score.toFixed(2)}</span>
        </div>
      </header>
      {actors ? <p className="framing-actors">Actors: {actors}</p> : null}
      {f.analysis_notes ? (
        <div className="framing-notes-wrap">
          <span className="framing-notes-kicker">Analyst notes</span>
          <p className="framing-notes">{f.analysis_notes}</p>
        </div>
      ) : null}
      <div className="framing-chips">
        {f.emphasis_terms.slice(0, 14).map((t) => (
          <span key={t} className="chip chip--term">
            {t}
          </span>
        ))}
      </div>
      {f.omission_candidates.length ? (
        <div className="framing-omissions">
          <span className="omissions-label">Omission signals</span>
          <ul>
            {f.omission_candidates.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {f.evidence.length ? (
        <details className="framing-evidence">
          <summary>Grounded evidence</summary>
          <ul>
            {f.evidence.map((ev) => (
              <li key={ev.quote}>
                <span className="ev-role">{ev.role}</span>
                <q>{ev.quote}</q>
              </li>
            ))}
          </ul>
        </details>
      ) : (
        <p className="framing-evidence-empty">
          No verbatim evidence spans for this source. The model may have omitted quotes, or none matched the
          source text after validation.
        </p>
      )}
    </article>
  );
}
