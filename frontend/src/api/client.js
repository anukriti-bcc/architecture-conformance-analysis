// Talks to the FastAPI backend via the /api proxy set up in vite.config.js
// (see server.proxy) — so this file never needs to know the backend's
// host/port and CORS is a non-issue in dev.

const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body.detail || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return res.json();
}

export function analyzeRepository(repositoryPath, architectureFile) {
  return request("/repositories/analyze", {
    method: "POST",
    body: JSON.stringify({
      repository_path: repositoryPath,
      architecture_file: architectureFile,
    }),
  });
}

export function getAnalysis(analysisId) {
  return request(`/analysis/${analysisId}`);
}

export function getAnalysisGraph(analysisId) {
  return request(`/analysis/${analysisId}/graph`);
}

export function getAnalysisFindings(analysisId) {
  return request(`/analysis/${analysisId}/findings`);
}

export function getFinding(findingId) {
  return request(`/findings/${findingId}`);
}

export function getFindingEvolution(findingId) {
  return request(`/findings/${findingId}/evolution`);
}

export function requestSemanticAnalysis(findingId) {
  return request(`/findings/${findingId}/semantic-analysis`, { method: "POST" });
}
