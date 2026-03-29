const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  code: string;
  details?: unknown;
  retryable?: boolean;

  constructor(message: string, code = "API_ERROR", details?: unknown, retryable = false) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.retryable = retryable;
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
      cache: "no-store",
    });

    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      throw new ApiError(
        typeof data === "object" && data && "message" in data ? String(data.message) : `Request failed: ${response.status}`,
        `HTTP_${response.status}`,
        data,
        response.status >= 500
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Request timed out", "TIMEOUT", undefined, true);
    }
    throw new ApiError("Unexpected network error", "NETWORK_ERROR", error, true);
  } finally {
    clearTimeout(timeout);
  }
}
