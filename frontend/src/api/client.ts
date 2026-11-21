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

/**
 * WebSocket URL for a path like "/ws/chat/7/". Uses the API host in dev
 * (VITE_API_URL) or the page's own host in production (VITE_API_URL empty).
 */
export function wsUrl(path: string): string {
  const base = BASE_URL || window.location.origin;
  return base.replace(/^http/, "ws") + path;
}

/** Converts a raw WebSocket JSON payload to camelCase like API responses. */
export function fromServer<T>(data: unknown): T {
  return convertKeys(data, toCamel) as T;
}

/** Thrown for any non-2xx response. `data` is the (camelCased) JSON error body. */
export class ApiError extends Error {
  status: number;
  data: Record<string, unknown>;

  constructor(status: number, data: Record<string, unknown>) {
    super(`Request failed: ${status}`);
    this.status = status;
    this.data = data;
  }
}

/**
 * Full URL for an uploaded file. The API returns "/media/..." paths (files on
 * the API server's disk), so in dev they need the API host in front; full
 * URLs (e.g. S3 later) are used as they are.
 */
export function mediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  return /^https?:\/\//.test(url) ? url : `${BASE_URL}${url}`;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = localStorage.getItem("token");
  // FormData (file uploads) is sent as-is: the browser sets the multipart
  // Content-Type itself. Everything else is JSON with snake_case keys.
  const isForm = body instanceof FormData;
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        ...(isForm ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Token ${token}` } : {}),
      },
      body:
        body === undefined ? undefined : isForm ? body : JSON.stringify(convertKeys(body, toSnake)),
    });
  } catch {
    // fetch only throws when the server can't be reached at all.
    throw new ApiError(0, { detail: "Can't reach the server. Is the backend running?" });
  }
  if (res.status === 204) return undefined as T;
  // Nginx rejects bodies over its limit before Django sees them (no JSON).
  if (res.status === 413) {
    throw new ApiError(413, { detail: "That file is too large. The maximum size is 10 MB." });
  }
  const json = convertKeys(await res.json().catch(() => ({})), toCamel);
  if (!res.ok) throw new ApiError(res.status, json as Record<string, unknown>);
  return json as T;
}

export const apiGet = <T>(path: string) => request<T>("GET", path);
export const apiPost = <T>(path: string, body?: unknown) => request<T>("POST", path, body);
export const apiPut = <T>(path: string, body?: unknown) => request<T>("PUT", path, body);
export const apiDelete = <T>(path: string) => request<T>("DELETE", path);
/** Multipart POST, for file uploads. */
export const apiUpload = <T>(path: string, form: FormData) => request<T>("POST", path, form);

/** First error message per field, e.g. { schoolEmail: "Please use your .edu school email." } */
export function fieldErrors(err: unknown): Record<string, string> {
  if (!(err instanceof ApiError)) return {};
  const out: Record<string, string> = {};
  for (const [field, value] of Object.entries(err.data)) {
    // nonFieldErrors isn't a form field; errorMessage() handles it.
    if (field === "nonFieldErrors") continue;
    if (Array.isArray(value) && typeof value[0] === "string") out[field] = value[0];
    // List fields report per-item errors keyed by index: {"0": ["Enter a valid URL."]}
    else if (value && typeof value === "object") {
      const first = Object.values(value as Record<string, unknown>)[0];
      if (Array.isArray(first) && typeof first[0] === "string") out[field] = first[0];
    }
  }
  return out;
}

/** One human-readable message for errors that aren't tied to a form field. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const { detail, nonFieldErrors } = err.data as {
      detail?: string;
      nonFieldErrors?: string[];
    };
    if (detail) return detail;
    if (nonFieldErrors?.length) return nonFieldErrors[0];
  }
  return "Something went wrong. Please try again.";
}
