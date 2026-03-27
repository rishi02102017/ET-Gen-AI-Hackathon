import { useEffect, useState } from "react";
import { fetchHealth } from "../api/client";
import type { HealthPayload } from "../types";

const POLL_MS = 60_000;

export function ApiStatusChip() {
  const [health, setHealth] = useState<HealthPayload | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const h = await fetchHealth();
      if (!cancelled) setHealth(h);
    }
    void load();
    const t = window.setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, []);

  if (health === null) {
    return (
      <div className="api-status api-status--unknown" title="API status unknown (is the backend running?)">
        <span className="api-status-dot" aria-hidden />
        API …
      </div>
    );
  }

  const live = health.llm_mode === "live";
  const host = health.llm_api_host ? ` · ${health.llm_api_host}` : "";

  return (
    <div
      className={`api-status ${live ? "api-status--live" : "api-status--mock"}`}
      title={`Pipeline ${health.pipeline_version}${host}${health.llm_fallback_ready ? " · Fallback ready" : ""}`}
    >
      <span className="api-status-dot" aria-hidden />
      <span className="api-status-text">
        {live ? "Live" : "Mock"} · v{health.pipeline_version}
      </span>
      {health.llm_fallback_ready ? (
        <span className="api-status-fb" title="Groq backup configured">
          FB
        </span>
      ) : null}
    </div>
  );
}
