import { api } from "../../api/client";

const mockFetch = jest.fn();
global.fetch = mockFetch;

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe("api client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    sessionStorage.clear();
    delete (window as { location?: Location }).location;
    window.location = { pathname: "/profile", href: "" } as Location;
  });

  it("gửi Authorization khi có token", async () => {
    sessionStorage.setItem("sv_access_token", "token-abc");
    mockFetch.mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await api.get("/me");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-abc");
  });

  it("POST gửi JSON và Content-Type", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ success: true, data: { id: 1 } }),
    );

    await api.post("/auth/login", { email: "a@b.com", password: "secret" });

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/auth/login");
    expect(init.method).toBe("POST");
    const headers = init.headers as Headers;
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init.body).toBe(
      JSON.stringify({ email: "a@b.com", password: "secret" }),
    );
  });

  it("trả về body khi response ok", async () => {
    const payload = { success: true, data: { access_token: "t1" } };
    mockFetch.mockResolvedValue(jsonResponse(payload));

    const result = await api.post("/auth/login", { email: "x", password: "y" });
    expect(result).toEqual(payload);
  });

  it("ném lỗi với message từ API", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse(
        {
          success: false,
          error: {
            code: "AUTH_LOGIN_FAILED",
            message: "Sai mật khẩu",
            details: [],
          },
        },
        401,
      ),
    );

    await expect(api.post("/auth/login", {})).rejects.toThrow("Sai mật khẩu");
  });

  it("xóa token và chuyển /login khi 401", async () => {
    sessionStorage.setItem("sv_access_token", "expired");
    window.location = { pathname: "/profile", href: "" } as Location;
    mockFetch.mockResolvedValue(
      jsonResponse(
        { success: false, error: { message: "Unauthorized", details: [] } },
        401,
      ),
    );

    await expect(api.get("/me")).rejects.toThrow();
    expect(sessionStorage.getItem("sv_access_token")).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  it("không redirect 401 khi đang ở /login", async () => {
    sessionStorage.setItem("sv_access_token", "expired");
    window.location = { pathname: "/login", href: "/login" } as Location;
    mockFetch.mockResolvedValue(
      jsonResponse({ error: { message: "Unauthorized" } }, 401),
    );

    await expect(api.get("/me")).rejects.toThrow();
    expect(window.location.href).toBe("/login");
  });

  it("xử lý JSON parse lỗi", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("invalid json");
      },
    });

    await expect(api.get("/me")).rejects.toThrow(
      "Lỗi xử lý phản hồi từ hệ thống.",
    );
  });
});
