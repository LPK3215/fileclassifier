const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body?.detail || `Request failed: ${response.status}`);
  }
  return body;
}

export async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body?.detail || `Request failed: ${response.status}`);
  }
  return body;
}
