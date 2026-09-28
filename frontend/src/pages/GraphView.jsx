import React, { useEffect, useMemo, useState } from "react";
import { getAnalysisGraph } from "../api/client.js";

// Typical layered-architecture flow, top to bottom. Any architectural
// type not listed here (custom component_mapping entries) is appended
// after these, in first-seen order — so the layout still works for
// architectures this list doesn't anticipate.
const LAYER_ORDER = ["frontend", "controller", "service", "repository", "model", "database"];

const NODE_W = 190;
const NODE_H = 40;
const COL_GAP = 34;
const ROW_GAP = 84;
const MARGIN = 48;

function layout(nodes) {
  const byType = new Map();
  for (const n of nodes) {
    const t = n.architectural_type || "unknown";
    if (!byType.has(t)) byType.set(t, []);
    byType.get(t).push(n);
  }

  const types = [...byType.keys()].sort((a, b) => {
    const ia = LAYER_ORDER.indexOf(a);
    const ib = LAYER_ORDER.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });

  const positions = {};
  let maxRowWidth = 0;

  types.forEach((type, rowIdx) => {
    const rowNodes = byType.get(type);
    const rowWidth = rowNodes.length * NODE_W + (rowNodes.length - 1) * COL_GAP;
    maxRowWidth = Math.max(maxRowWidth, rowWidth);
    const y = MARGIN + rowIdx * (NODE_H + ROW_GAP);
    rowNodes.forEach((node, colIdx) => {
      const x = colIdx * (NODE_W + COL_GAP);
      positions[node.id] = { x, y, type };
    });
  });

  // center each row within the widest row
  types.forEach((type) => {
    const rowNodes = byType.get(type);
    const rowWidth = rowNodes.length * NODE_W + (rowNodes.length - 1) * COL_GAP;
    const offset = (maxRowWidth - rowWidth) / 2;
    rowNodes.forEach((node) => {
      positions[node.id].x += offset + MARGIN;
    });
  });

  const width = maxRowWidth + MARGIN * 2;
  const height = MARGIN * 2 + types.length * (NODE_H + ROW_GAP) - ROW_GAP;

  return { positions, width, height, types };
}

export default function GraphView({ analysisId }) {
  const [graph, setGraph] = useState(null);
  const [error, setError] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  // Hidden by default — files with no import edges at all (mostly
  // __init__.py) add clutter without adding information to a dependency
  // graph specifically. They're still counted in the Overview stats;
  // this only affects what's drawn here.
  const [showIsolated, setShowIsolated] = useState(false);

  useEffect(() => {
    setGraph(null);
    setError(null);
    getAnalysisGraph(analysisId)
      .then(setGraph)
      .catch((err) => setError(err.message));
  }, [analysisId]);

  const { visibleNodes, isolatedCount } = useMemo(() => {
    if (!graph) return { visibleNodes: [], isolatedCount: 0 };
    const connected = new Set();
    for (const edge of graph.edges) {
      connected.add(edge.source);
      connected.add(edge.target);
    }
    const isolated = graph.nodes.filter((n) => !connected.has(n.id));
    const visible = showIsolated ? graph.nodes : graph.nodes.filter((n) => connected.has(n.id));
    return { visibleNodes: visible, isolatedCount: isolated.length };
  }, [graph, showIsolated]);

  const layoutResult = useMemo(() => {
    if (!graph) return null;
    return layout(visibleNodes);
  }, [graph, visibleNodes]);

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Dependency graph</h1>
        </div>
        <div className="error-banner">{error}</div>
      </div>
    );
  }

  if (!graph || !layoutResult) {
    return <p className="empty-state">Loading graph…</p>;
  }

  const { positions, width, height } = layoutResult;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dependency graph</h1>
        <p className="page-desc">
          Nodes are implementation files, grouped by row into their
          architectural role. Edges are observed <code className="mono">import</code>{" "}
          dependencies. Rows are ordered by architectural role, not by a
          layout algorithm.
        </p>
      </div>

      <div className="legend" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: 20 }}>
          <span>
            <span className="legend-swatch" style={{ background: "#3cae55" }} />
            conformant
          </span>
          <span>
            <span className="legend-swatch" style={{ background: "#e5472b" }} />
            violation
          </span>
        </div>
        {isolatedCount > 0 && (
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showIsolated}
              onChange={(e) => setShowIsolated(e.target.checked)}
            />
            show {isolatedCount} file{isolatedCount === 1 ? "" : "s"} with no dependencies
          </label>
        )}
      </div>

      <div className="graph-canvas-wrap" style={{ height: 520 }}>
        <svg width={width} height={height}>
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3cae55" />
            </marker>
            <marker
              id="arrow-violation"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#e5472b" />
            </marker>
          </defs>

          {graph.edges.map((edge, i) => {
            const s = positions[edge.source];
            const t = positions[edge.target];
            if (!s || !t) return null;
            const x1 = s.x + NODE_W / 2;
            const y1 = s.y + NODE_H;
            const x2 = t.x + NODE_W / 2;
            const y2 = t.y;
            const midY = (y1 + y2) / 2;
            const path = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
            const isSelected =
              selectedEdge &&
              selectedEdge.source === edge.source &&
              selectedEdge.target === edge.target;

            return (
              <path
                key={i}
                d={path}
                fill="none"
                stroke={edge.is_violation ? "#e5472b" : "#3cae55"}
                strokeWidth={isSelected ? 4 : edge.is_violation ? 3 : 2}
                markerEnd={`url(#${edge.is_violation ? "arrow-violation" : "arrow"})`}
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedEdge(edge)}
              />
            );
          })}

          {visibleNodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;
            return (
              <g key={node.id} transform={`translate(${pos.x}, ${pos.y})`}>
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  rx={4}
                  fill="#17130f"
                  stroke="#3a2f24"
                />
                <text
                  x={10}
                  y={17}
                  fill="#ede1cd"
                  fontSize={12}
                  fontFamily="JetBrains Mono, monospace"
                >
                  {truncate(node.name, 22)}
                </text>
                <text
                  x={10}
                  y={31}
                  fill="#8f7d68"
                  fontSize={10}
                  fontFamily="Inter, sans-serif"
                >
                  {node.architectural_type}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {selectedEdge && (
        <div className="panel" style={{ marginTop: 16 }}>
          <h4 style={{ margin: "0 0 8px 0", fontFamily: "var(--font-display)", fontSize: 13 }}>
            {selectedEdge.is_violation ? "Violating edge" : "Edge"}
          </h4>
          <div className="mono" style={{ fontSize: 12.5, color: "var(--muted)" }}>
            {selectedEdge.source} → {selectedEdge.target}
            <br />
            {selectedEdge.source_component} → {selectedEdge.target_component} (
            {selectedEdge.dependency_type})
          </div>
        </div>
      )}
    </div>
  );
}

function truncate(str, n) {
  return str.length > n ? str.slice(0, n - 1) + "…" : str;
}
