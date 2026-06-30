const API_BASE = "";

export async function fetchClients(params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.append(key, value);
    }
  }
  const qs = query.toString();
  const res = await fetch(`${API_BASE}/clients${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error(`fetchClients failed: ${res.status}`);
  return res.json();
}

export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/clients/status`);
  if (!res.ok) throw new Error(`fetchStatus failed: ${res.status}`);
  return res.json();
}

export async function fetchMetric(name, params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.append(key, value);
    }
  }
  const qs = query.toString();
  const res = await fetch(`${API_BASE}/metrics/${name}${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error(`fetchMetric ${name} failed: ${res.status}`);
  return res.json();
}

export async function fetchInsight(chartType) {
  const res = await fetch(`${API_BASE}/insights/${chartType}`);
  if (!res.ok)
    throw new Error(`fetchInsight ${chartType} failed: ${res.status}`);
  return res.json();
}
