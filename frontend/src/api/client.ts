const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const toCamel = (s: string) => s.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
const toSnake = (s: string) => s.replace(/[A-Z]/g, (c) => "_" + c.toLowerCase());

function convertKeys(data: unknown, fn: (k: string) => string): unknown {
  if (Array.isArray(data)) return data.map((d) => convertKeys(d, fn));
  if (data && typeof data === "object") {
    return Object.fromEntries(
      Object.entries(data as Record<string, unknown>).map(([k, v]) => [fn(k), convertKeys(v, fn)])
    );
  }
  return data;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = localStorage.getItem("token");
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Token ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(convertKeys(body, toSnake)),
  });
  if (!res.ok) throw new Error(`${method} ${path} failed: ${res.status}`);
  if (res.status === 204) return undefined as T;
  return convertKeys(await res.json(), toCamel) as T;
}

export const apiGet = <T>(path: string) => request<T>("GET", path);
export const apiPost = <T>(path: string, body?: unknown) => request<T>("POST", path, body);
export const apiPut = <T>(path: string, body?: unknown) => request<T>("PUT", path, body);
export const apiDelete = <T>(path: string) => request<T>("DELETE", path);
