import { useEffect, useState } from "react";

const PHASES = [
  "Ingesting corpus",
  "Extracting narrative signals",
  "Aligning cross-source event",
  "Scoring stance and emphasis",
  "Computing divergence index",
];

type Props = { active: boolean };

export function LoadingExperience({ active }: Props) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    if (!active) {
      setPhase(0);
      return;
    }
    const id = window.setInterval(() => {
      setPhase((p) => (p + 1) % PHASES.length);
    }, 1400);
    return () => window.clearInterval(id);
  }, [active]);

  if (!active) return null;

  return (
    <div className="loading-overlay" role="status" aria-live="polite" aria-busy="true">
      <div className="loading-panel">
        <div className="loading-spinner" aria-hidden />
        <div className="loading-copy">
          <p className="loading-title">Analyzing framing</p>
          <p className="loading-phase">{PHASES[phase]}</p>
          <p className="loading-hint">Multi-source comparison may take up to a minute.</p>
        </div>
        <div className="loading-skeleton">
          <div className="sk-line sk-w-90" />
          <div className="sk-line sk-w-70" />
          <div className="sk-line sk-w-80" />
          <div className="sk-blocks">
            <div className="sk-block" />
            <div className="sk-block" />
            <div className="sk-block" />
          </div>
        </div>
        <div className="loading-steps">
          {PHASES.map((label, i) => (
            <span
              key={label}
              className={`loading-step-dot ${i === phase ? "loading-step-dot--on" : ""} ${i < phase ? "loading-step-dot--done" : ""}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
