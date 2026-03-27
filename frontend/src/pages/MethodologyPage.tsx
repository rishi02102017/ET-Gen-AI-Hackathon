import { Link } from "react-router-dom";
import "../App.css";

export function MethodologyPage() {
  return (
    <main className="main methodology-page">
      <header className="methodology-page-hero">
        <p className="hero-eyebrow">Documentation</p>
        <h1 className="methodology-page-title">Methodology</h1>
        <p className="methodology-page-lead">
          How FrameAtlas turns a multi-source corpus into comparable framing signals and a single,
          auditable divergence index—without claiming ground truth about facts.
        </p>
      </header>

      <div className="methodology-page-body">
        <section className="methodology-block" aria-labelledby="philosophy-heading">
          <h2 id="philosophy-heading" className="methodology-h2">
            Design philosophy
          </h2>
          <p className="methodology-prose">
            Professional news-intelligence tools separate <strong>what happened</strong> from{" "}
            <strong>how it is told</strong>. FrameAtlas is explicitly in the second category: it
            surfaces stance, emphasis, actor casting, and cross-source gaps so analysts can reason
            about narrative—not replace editorial judgment or fact-checking.
          </p>
        </section>

        <section className="methodology-block" aria-labelledby="pipeline-heading">
          <h2 id="pipeline-heading" className="methodology-h2">
            Pipeline
          </h2>
          <ol className="methodology-steps methodology-steps--page">
            <li>
              <span className="method-step-num">01</span>
              <div>
                <h3>Ingestion</h3>
                <p>
                  Public URLs are fetched with SSRF safeguards and size limits. Operators may paste
                  full text when paywalls or robots policies block retrieval. Each document is
                  normalized and fingerprinted (SHA-256) for traceability.
                </p>
              </div>
            </li>
            <li>
              <span className="method-step-num">02</span>
              <div>
                <h3>Event alignment</h3>
                <p>
                  A neutral event hypothesis—title, summary, and key entities—anchors all sources to
                  a shared referent so downstream comparisons are about framing relative to the same
                  story, not unrelated articles.
                </p>
              </div>
            </li>
            <li>
              <span className="method-step-num">03</span>
              <div>
                <h3>Structured framing inference</h3>
                <p>
                  A temperature-controlled, JSON-constrained language model pass extracts per-source
                  stance, sentiment, salient terms, atomic claims, omission candidates, and short
                  evidence quotes. Invalid or partial model output is repaired or falls back to a
                  deterministic mock path for reproducibility.
                </p>
              </div>
            </li>
            <li>
              <span className="method-step-num">04</span>
              <div>
                <h3>Deterministic divergence</h3>
                <p>
                  Subscores—stance spread, emphasis mismatch, a blend of claim-coverage balance and
                  cross-source omission spread, and actor framing delta—are fused with published
                  weights into a 0–100 index. Evidence quotes are filtered to verbatim source text.
                  That separation
                  keeps the headline number explainable and stable across model versions.
                </p>
              </div>
            </li>
          </ol>
        </section>

        <section className="methodology-block" aria-labelledby="limits-heading">
          <h2 id="limits-heading" className="methodology-h2">
            Limitations
          </h2>
          <ul className="methodology-list">
            <li>Short or boilerplate extracts reduce confidence; prefer pasted body text when needed.</li>
            <li>Stance labels are model-dependent and should be read with evidence spans.</li>
            <li>The index measures narrative divergence, not factual falsehood or malice.</li>
          </ul>
        </section>

        <div className="methodology-cta card">
          <div>
            <h2 className="methodology-cta-title">Ready to run a comparison?</h2>
            <p className="methodology-cta-copy">
              Return to the workspace to ingest sources and generate a full briefing.
            </p>
          </div>
          <Link to="/" className="btn btn--primary methodology-cta-btn">
            Go to workspace
          </Link>
        </div>
      </div>
    </main>
  );
}
