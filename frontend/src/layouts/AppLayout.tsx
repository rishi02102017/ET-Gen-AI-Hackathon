import { Link, NavLink, Outlet } from "react-router-dom";
import { ApiStatusChip } from "../components/ApiStatusChip";
import { GITHUB_REPO_URL } from "../config/public";

export function AppLayout() {
  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <div className="app-bg" aria-hidden />
      <div className="app-grid" aria-hidden />

      <header className="top-nav">
        <div className="top-nav-inner">
          <Link to="/" className="brand" aria-label="FrameAtlas — home">
            <span className="brand-mark" aria-hidden />
            <div className="brand-text">
              <span className="brand-name">FrameAtlas</span>
              <span className="brand-tag">Narrative intelligence</span>
            </div>
          </Link>
          <div className="top-nav-right">
            <ApiStatusChip />
            <nav className="top-nav-links" aria-label="Primary">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `nav-pill ${isActive ? "nav-pill--active" : "nav-pill--muted"}`
                }
              >
                Workspace
              </NavLink>
              <NavLink
                to="/methodology"
                className={({ isActive }) =>
                  `nav-pill ${isActive ? "nav-pill--active" : "nav-pill--muted"}`
                }
              >
                Methodology
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      <Outlet />

      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-col footer-col--disclaimer">
            <p>
              FrameAtlas surfaces <strong>framing</strong>, not factual verdicts. Results depend on model
              and corpus quality; always corroborate with primary reporting.
            </p>
          </div>
          <nav className="footer-links" aria-label="Footer">
            <Link to="/methodology" className="footer-link">
              Methodology
            </Link>
            <a href={GITHUB_REPO_URL} className="footer-link" target="_blank" rel="noreferrer">
              GitHub
            </a>
            <Link to="/" className="footer-link">
              Workspace
            </Link>
          </nav>
        </div>
        <p className="footer-hackathon">
          ET Gen AI Hackathon 2026 · Problem 8 · AI-native news experience
        </p>
      </footer>
    </div>
  );
}
