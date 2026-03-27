import { Link, NavLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="app">
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
      </header>

      <Outlet />

      <footer className="footer">
        <p>
          FrameAtlas surfaces <strong>framing</strong>, not factual verdicts. Results depend on model
          and corpus quality; always corroborate with primary reporting.
        </p>
      </footer>
    </div>
  );
}
