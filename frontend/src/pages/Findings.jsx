import React, { useEffect, useState } from "react";
import { getAnalysisFindings, getFinding } from "../api/client.js";

export default function Findings({ analysisId }) {
  const [findings, setFindings] = useState(null);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    setFindings(null);
    setSelectedId(null);
    getAnalysisFindings(analysisId)
      .then(setFindings)
      .catch((err) => setError(err.message));
  }, [analysisId]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!findings) return <p className="empty-state">Loading findings…</p>;

  if (selectedId) {
    return <FindingDetail findingId={selectedId} onBack={() => setSelectedId(null)} />;
  }

  const violations = findings.filter((f) => f.status === "violation");
  const conformant = findings.filter((f) => f.status === "conformant");

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Findings</h1>
        <p className="page-desc">
          One row per governed dependency ({violations.length} violation
          {violations.length === 1 ? "" : "s"}, {conformant.length} conformant).
          Dependencies with no applicable rule at all are omitted here — the
          engine doesn't guess at unspecified relationships.
        </p>
      </div>

      <table className="findings-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Source</th>
            <th>Target</th>
            <th>Rule</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <tr key={f.id} className="clickable" onClick={() => setSelectedId(f.id)}>
              <td>
                <span className={`status-pill ${f.status}`}>{f.status}</span>
              </td>
              <td>
                <div className="mono">{f.source.name}</div>
                <div style={{ color: "var(--muted-dim)", fontSize: 11 }}>
                  {f.source.component}
                </div>
              </td>
              <td>
                <div className="mono">{f.target.name}</div>
                <div style={{ color: "var(--muted-dim)", fontSize: 11 }}>
                  {f.target.component}
                </div>
              </td>
              <td className="mono" style={{ color: "var(--muted)" }}>
                {f.rule_id}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FindingDetail({ findingId, onBack }) {
  const [finding, setFinding] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setFinding(null);
    getFinding(findingId)
      .then(setFinding)
      .catch((err) => setError(err.message));
  }, [findingId]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!finding) return <p className="empty-state">Loading…</p>;

  return (
    <div>
      <button className="back-link" onClick={onBack}>
        ← back to findings
      </button>

      <div className="page-header">
        <h1 className="page-title">
          {finding.id}{" "}
          <span className={`status-pill ${finding.status}`} style={{ marginLeft: 10 }}>
            {finding.status}
          </span>
        </h1>
        <p className="page-desc">{finding.expected}</p>
      </div>

      <div className="panel">
        <div style={{ display: "flex", gap: 40, marginBottom: 4 }}>
          <div>
            <div style={{ color: "var(--muted)", fontSize: 12 }}>Source</div>
            <div className="mono">{finding.source.name}</div>
            <div style={{ color: "var(--muted-dim)", fontSize: 11 }}>
              {finding.source.component} · {finding.source.id}
            </div>
          </div>
          <div>
            <div style={{ color: "var(--muted)", fontSize: 12 }}>Target</div>
            <div className="mono">{finding.target.name}</div>
            <div style={{ color: "var(--muted-dim)", fontSize: 11 }}>
              {finding.target.component} · {finding.target.id}
            </div>
          </div>
          {finding.location && (
            <div>
              <div style={{ color: "var(--muted)", fontSize: 12 }}>Location</div>
              <div className="mono">
                {finding.location.file}:{finding.location.line}
              </div>
            </div>
          )}
          <div>
            <div style={{ color: "var(--muted)", fontSize: 12 }}>Rule</div>
            <div className="mono">{finding.rule_id}</div>
          </div>
        </div>
      </div>

      <h4
        style={{
          fontFamily: "var(--font-display)",
          fontSize: 12.5,
          color: "var(--muted)",
          marginTop: 26,
          marginBottom: 0,
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        Evidence
      </h4>
      <div className="detail-grid">
        <EvidenceBlock title="Structural evidence" data={finding.structural_evidence} />
        <EvidenceBlock
          title="Evolution evidence"
          data={finding.evolution_evidence}
          emptyNote="Not yet analyzed."
        />
        <EvidenceBlock
          title="Semantic analysis"
          data={finding.semantic_analysis}
          emptyNote="Not yet analyzed."
        />
        <EvidenceBlock
          title="Decision"
          data={finding.decision}
          emptyNote="No escalation policy defined yet."
        />
      </div>
    </div>
  );
}

function EvidenceBlock({ title, data, emptyNote }) {
  return (
    <div className="detail-block">
      <h4>{title}</h4>
      {data ? (
        <pre
          className="mono"
          style={{
            margin: 0,
            fontSize: 11.5,
            color: "var(--text)",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : (
        <div className="empty">{emptyNote || "—"}</div>
      )}
    </div>
  );
}
