import type { APIErrorDetail, APIResponse } from "./client";

interface PaginatedListMeta {
  page: number;
  page_size: number;
  total: number;
}

export interface AdminClientError extends Error {
  code?: string;
}

const API_BASE_URL = "/api";

function isPaginatedResponse(
  value: unknown,
): value is APIResponse<unknown[]> & { meta: PaginatedListMeta } {
  if (typeof value !== "object" || value === null) return false;
  const record = value as APIResponse<unknown[]>;
  return (
    record.success === true &&
    Array.isArray(record.data) &&
    "meta" in value &&
    typeof (value as { meta: unknown }).meta === "object"
  );
}

function extractErrorDetail(
  payload: APIResponse<unknown> & { detail?: unknown },
): APIErrorDetail {
  if (payload.error) return payload.error;
  const detail = payload.detail;
  if (
    typeof detail === "object" &&
    detail !== null &&
    "error" in detail &&
    typeof (detail as { error: unknown }).error === "object" &&
    (detail as { error: APIErrorDetail }).error !== null
  ) {
    return (detail as { error: APIErrorDetail }).error;
  }
  return {
    code: "HTTP_ERROR",
    message:
      typeof payload.detail === "string" ? payload.detail : "Đã xảy ra lỗi.",
    details: [],
  };
}

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
    result = (await response.json()) as
      | APIResponse<T>
      | Record<string, unknown>;
  } catch {
    result = {
      success: false,
      error: {
        code: "PARSE_ERROR",
        message: "Lỗi xử lý phản hồi từ hệ thống.",
        details: [],
      },
    };
  }

  if (!response.ok) {
    const errorDetail = extractErrorDetail(
      result as APIResponse<unknown> & { detail?: unknown },
    );
    const err = new Error(
      errorDetail.message || "Đã xảy ra lỗi.",
    ) as AdminClientError;
    err.code = errorDetail.code;
    throw err;
  }

  if (isPaginatedResponse(result)) {
    return {
      success: true,
      data: {
        data: result.data,
        meta: result.meta,
      },
    } as APIResponse<T>;
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

  post: <T = unknown>(
    endpoint: string,
    body?: unknown,
    options?: RequestInit,
  ) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(
    endpoint: string,
    body?: unknown,
    options?: RequestInit,
  ) =>
    request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T = unknown>(
    endpoint: string,
    body?: unknown,
    options?: RequestInit,
  ) =>
    request<T>(endpoint, {
      ...options,
      method: "DELETE",
      body: body ? JSON.stringify(body) : undefined,
    }),

  getBlob: (endpoint: string) => requestBlob(endpoint),
};
