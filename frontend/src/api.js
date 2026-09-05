const TOKEN_KEY = "cc_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (resp.status === 401) {
    setToken(null);
    window.location.href = "/login";
    throw new Error("Not authenticated");
  }
  if (resp.status === 204) return null;

  const data = await resp.json().catch(() => null);
  if (resp.ok && Array.isArray(data)) {
    const total = resp.headers.get("X-Total-Count");
    if (total !== null) data.totalCount = Number(total);
  }
  if (!resp.ok) {
    const detail = data && data.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join("; ")
          : `Request failed (${resp.status})`;
    throw new Error(msg);
  }
  return data;
}
