import { adminApi } from "../../api/adminClient";

const mockFetch = jest.fn();
global.fetch = mockFetch;

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe("adminClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    sessionStorage.clear();
    delete (window as { location?: Location }).location;
    window.location = { pathname: "/admin", href: "" } as Location;
  });

  it("gửi Authorization khi có admin_access_token", async () => {
    sessionStorage.setItem("admin_access_token", "admin-tok");
    mockFetch.mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await adminApi.get("/admin/auth/me");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer admin-tok");
  });

  it("không gửi Authorization khi không có token", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await adminApi.get("/admin/auth/me");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
  });

  it("POST gửi JSON body", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ success: true, data: { access_token: "t1" } }),
    );

    await adminApi.post("/admin/auth/login", { username: "admin", password: "pass" });

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/admin/auth/login");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ username: "admin", password: "pass" }));
  });

  it("xóa token và chuyển /admin/login khi 401", async () => {
    sessionStorage.setItem("admin_access_token", "expired");
    window.location = { pathname: "/admin/dashboard", href: "" } as Location;
    mockFetch.mockResolvedValue(
      jsonResponse(
        { success: false, error: { code: "UNAUTHORIZED", message: "Token hết hạn", details: [] } },
        401,
      ),
    );

    await expect(adminApi.get("/admin/auth/me")).rejects.toThrow();
    expect(sessionStorage.getItem("admin_access_token")).toBeNull();
    expect(window.location.href).toBe("/admin/login");
  });

  it("không redirect 401 khi đang ở /admin/login", async () => {
    sessionStorage.setItem("admin_access_token", "expired");
    window.location = { pathname: "/admin/login", href: "/admin/login" } as Location;
    mockFetch.mockResolvedValue(
      jsonResponse({ success: false, error: { message: "Unauthorized", details: [] } }, 401),
    );

    await expect(adminApi.get("/admin/auth/me")).rejects.toThrow();
    expect(window.location.href).toBe("/admin/login");
  });

  it("ném lỗi với message từ API response", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse(
        { success: false, error: { code: "RATE_LIMIT", message: "Quá nhiều lần thử", details: [] } },
        429,
      ),
    );

    await expect(adminApi.post("/admin/auth/login", {})).rejects.toThrow("Quá nhiều lần thử");
  });

  it("xử lý JSON parse lỗi", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new Error("invalid json"); },
    });

    await expect(adminApi.get("/admin/dashboard/stats")).rejects.toThrow(
      "Lỗi xử lý phản hồi từ hệ thống.",
    );
  });

  it("PATCH gửi đúng method", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await adminApi.patch("/admin/categories/cat001", { name: "Mới" });

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("PATCH");
  });

  it("DELETE gửi đúng method", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ success: true, data: null }));

    await adminApi.delete("/admin/categories/cat001");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("DELETE");
  });

  it("getBlob trả về blob khi thành công", async () => {
    const fakeBlob = new Blob(["csv data"], { type: "text/csv" });
    sessionStorage.setItem("admin_access_token", "tok");
    mockFetch.mockResolvedValue({ ok: true, status: 200, blob: async () => fakeBlob });

    const result = await adminApi.getBlob("/admin/audit-logs/export");
    expect(result).toBe(fakeBlob);
  });

  it("getBlob ném lỗi khi response không ok", async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500 });

    await expect(adminApi.getBlob("/admin/audit-logs/export")).rejects.toThrow(
      "Xuất dữ liệu thất bại.",
    );
  });
});
