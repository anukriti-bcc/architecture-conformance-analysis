import React, { useState } from "react";
import { analyzeRepository } from "../api/client.js";

export default function Overview({ analysis, onAnalyzed }) {
  const [repoPath, setRepoPath] = useState("../datasets/sample-ecommerce");
  const [archFile, setArchFile] = useState(
    "../datasets/sample-ecommerce/architecture/rules.yaml"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  async function handleAnalyze(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeRepository(repoPath, archFile);
      setLastResult(result);
      onAnalyzed({
        analysis_id: result.analysis_id,
        repository: result.repository,
        architecture: result.architecture,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const violationCount = lastResult
    ? lastResult.findings.filter((f) => f.status === "violation").length
    : null;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Repository analysis</h1>
        <p className="page-desc">
          Points a Tree-sitter-based scanner at a repository, resolves its
          import graph, and checks every observed dependency against an
          explicit architecture definition. Paths below are relative to
          the backend server's working directory.
        </p>
      </div>

      <form className="panel" onSubmit={handleAnalyze}>
        <div className="field-row">
          <div className="field">
            <label htmlFor="repoPath">Repository path</label>
            <input
              id="repoPath"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              spellCheck={false}
            />
          </div>
          <div className="field">
            <label htmlFor="archFile">Architecture file</label>
            <input
              id="archFile"
              value={archFile}
              onChange={(e) => setArchFile(e.target.value)}
              spellCheck={false}
            />
          </div>
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Analyzing…" : "Run analysis"}
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}
      </form>

      {lastResult && (
        <div className="stat-grid">
          <StatCard label="components" value={lastResult.components} />
          <StatCard label="dependencies" value={lastResult.dependencies} />
          <StatCard label="rules" value={lastResult.rules} />
          <StatCard
            label="violations"
            value={violationCount}
            tone={violationCount > 0 ? "brick" : "forest"}
          />
        </div>
      )}

      {!lastResult && !analysis && (
        <p className="empty-state">
          No analysis run yet. Run one above — the default paths point at
          the bundled demo repository (a small layered e-commerce backend
          with one deliberate architectural violation).
        </p>
      )}
    </div>
  );
}

function StatCard({ label, value, tone }) {
  return (
    <div className="stat-card">
      <div className={`stat-value ${tone || ""}`}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
