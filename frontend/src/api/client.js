const BASE = '/api';

export async function queryApi(query, context = null) {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, context }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchFacilities() {
  const res = await fetch(`${BASE}/facilities`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchSpecialties() {
  const res = await fetch(`${BASE}/specialties`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchPlanningScenarios() {
  const res = await fetch(`${BASE}/planning/scenarios`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function executePlanning(scenario, params = {}) {
  const res = await fetch(`${BASE}/planning/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, ...params }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchRoutingMap(scenario = 'emergency_routing', specialty = null, origin_city = null) {
  const res = await fetch(`${BASE}/routing-map`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, specialty, origin_city }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchMLOpsStatus() {
  const res = await fetch(`${BASE}/mlops/status`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchMLOpsPipeline() {
  const res = await fetch(`${BASE}/mlops/pipeline`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
