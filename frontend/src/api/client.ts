export interface APIErrorDetail {
  code: string;
  message: string;
  details: unknown[];
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  error?: APIErrorDetail;
}

const API_BASE_URL = "/api";

async function request<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<APIResponse<T>> {
  const token = sessionStorage.getItem("sv_access_token");

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (response.status === 401) {
    sessionStorage.removeItem("sv_access_token");
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
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
    const payload = result as APIResponse<T> & { detail?: string };
    const errorDetail = payload.error || {
      code: "HTTP_ERROR",
      message: payload.detail || "Đã xảy ra lỗi kết nối.",
      details: [],
    };
    throw new Error(errorDetail.message || "Đã xảy ra lỗi.");
  }

  return result as APIResponse<T>;
}

export const api = {
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

  postFormData: <T = unknown>(
    endpoint: string,
    formData: FormData,
    options?: RequestInit,
  ) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      body: formData,
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

  delete: <T = unknown>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),
};
