import type { APIErrorDetail, APIResponse } from "./client";

type RequestBody = any;

const API_BASE_URL = "/api";

async function request<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<APIResponse<T>> {
  const token = sessionStorage.getItem("admin_access_token");

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const config: RequestInit = { ...options, headers };
  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (response.status === 401) {
    sessionStorage.removeItem("admin_access_token");
    if (!window.location.pathname.startsWith("/admin/login")) {
      window.location.href = "/admin/login";
    }
  }

  if (response.status === 204) {
    return { success: true, data: null as unknown as T };
  }

  let result: APIResponse<T> | Record<string, unknown>;
  try {
    result = (await response.json()) as APIResponse<T> | Record<string, unknown>;
    console.log("[adminClient] Original parsed json for endpoint", endpoint, result);
  } catch {
    result = {
      success: false,
      error: { code: "PARSE_ERROR", message: "Lỗi xử lý phản hồi từ hệ thống.", details: [] },
    };
  }

  if (!response.ok) {
    const payload = result as APIResponse<T> & { detail?: unknown };
    let errorDetail: APIErrorDetail;
    if (payload.error) {
      errorDetail = payload.error;
    } else if (payload.detail && typeof payload.detail === "object" && (payload.detail as any).error) {
      errorDetail = (payload.detail as any).error;
    } else {
      errorDetail = {
        code: "HTTP_ERROR",
        message: typeof payload.detail === "string" ? payload.detail : "Đã xảy ra lỗi.",
        details: [],
      };
    }
    const err = new Error(errorDetail.message || "Đã xảy ra lỗi.");
    (err as any).code = errorDetail.code;
    throw err;
  }

  console.log("[adminClient] Conditions check:", {
    hasResult: !!result,
    isObject: typeof result === "object",
    success: result && (result as any).success,
    isArrayData: result && Array.isArray((result as any).data),
    hasMeta: result && !!(result as any).meta
  });

  if (
    result &&
    typeof result === "object" &&
    result.success &&
    Array.isArray(result.data) &&
    result.meta
  ) {
    result = {
      success: true,
      data: {
        data: result.data,
        meta: result.meta,
      },
    } as unknown as APIResponse<T>;
    console.log("[adminClient] Wrapped result:", result);
  }

  return result as APIResponse<T>;
}

async function requestBlob(endpoint: string): Promise<Blob> {
  const token = sessionStorage.getItem("admin_access_token");
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
  if (!response.ok) {
    throw new Error("Xuất dữ liệu thất bại.");
  }
  return response.blob();
}

export const adminApi = {
  get: <T = unknown>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: "GET" }),

  post: <T = unknown>(endpoint: string, body?: RequestBody, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(endpoint: string, body?: RequestBody, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T = unknown>(endpoint: string, body?: RequestBody, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: "DELETE",
      body: body ? JSON.stringify(body) : undefined,
    }),

  getBlob: (endpoint: string) => requestBlob(endpoint),
};
