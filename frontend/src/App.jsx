import React, { useState } from "react";
import Overview from "./pages/Overview.jsx";
import GraphView from "./pages/GraphView.jsx";
import Findings from "./pages/Findings.jsx";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", tick: "01" },
  { id: "graph", label: "Dependency Graph", tick: "02" },
  { id: "findings", label: "Findings", tick: "03" },
];

export default function App() {
  const [view, setView] = useState("overview");
  const [analysis, setAnalysis] = useState(null); // { analysis_id, ...summary }
  // index.html sets this attribute before React mounts (reading
  // localStorage) so there's no flash of the wrong theme — this just
  // picks up whatever it landed on.
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute("data-theme") || "dark"
  );

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (next === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    try {
      localStorage.setItem("theme", next);
    } catch (e) {
      /* localStorage unavailable — theme just won't persist across reloads */
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">Architecture Analysis Engine</div>
          <div className="brand-sub">structural conformance engine</div>
        </div>

        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => setView(item.id)}
              disabled={item.id !== "overview" && !analysis}
              title={
                item.id !== "overview" && !analysis
                  ? "Run an analysis first"
                  : undefined
              }
            >
              <span className="nav-tick">{item.tick}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button className="theme-toggle" onClick={toggleTheme}>
            <span className="theme-toggle-dot" />
            {theme === "dark" ? "switch to light" : "switch to dark"}
          </button>

          <div className="sidebar-footer">
            {analysis ? (
              <>
                run: {analysis.analysis_id}
                <br />
                {analysis.repository}
              </>
            ) : (
              "no analysis run yet"
            )}
          </div>
        </div>
      </aside>

      <main className="main">
        {view === "overview" && (
          <Overview
            analysis={analysis}
            onAnalyzed={(result) => {
              setAnalysis(result);
              setView("graph");
            }}
          />
        )}
        {view === "graph" && analysis && (
          <GraphView analysisId={analysis.analysis_id} />
        )}
        {view === "findings" && analysis && (
          <Findings analysisId={analysis.analysis_id} />
        )}
      </main>
    </div>
  );
}
