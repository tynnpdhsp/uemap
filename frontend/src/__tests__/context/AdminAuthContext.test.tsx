import { render, screen, waitFor, act } from "@testing-library/react";
import {
  AdminAuthProvider,
  useAdminAuth,
} from "../../context/AdminAuthContext";
import { adminAuthApi, type AdminInfo } from "../../api/admin/auth";
import type { APIResponse } from "../../api/client";

jest.mock("../../api/admin/auth", () => ({
  adminAuthApi: {
    login: jest.fn(),
    logout: jest.fn(),
    me: jest.fn(),
  },
}));

const mockedApi = adminAuthApi as jest.Mocked<typeof adminAuthApi>;

const adminProfile: AdminInfo = {
  id: "665000000000000000000001",
  username: "sysadmin",
  display_name: "Admin Test",
  is_system_admin: true,
  status: "active",
  status_label: "Hoạt động",
  last_login_at_display: "25/05/2025 10:00",
};

function Probe() {
  const auth = useAdminAuth();
  return (
    <div>
      <span data-testid="loading">{String(auth.loading)}</span>
      <span data-testid="authenticated">{String(auth.isAuthenticated)}</span>
      <span data-testid="name">{auth.admin?.display_name ?? ""}</span>
      <span data-testid="system-admin">
        {String(auth.admin?.is_system_admin ?? "")}
      </span>
      <button type="button" onClick={() => auth.login("sysadmin", "pass123")}>
        login
      </button>
      <button type="button" onClick={() => auth.logout()}>
        logout
      </button>
    </div>
  );
}

describe("AdminAuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
  });

  it("useAdminAuth ngoài Provider ném lỗi", () => {
    const Bad = () => {
      useAdminAuth();
      return null;
    };
    expect(() => render(<Bad />)).toThrow(
      "useAdminAuth phải được sử dụng trong AdminAuthProvider",
    );
  });

  it("không có token thì không gọi API và isAuthenticated = false", async () => {
    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
    expect(mockedApi.me).not.toHaveBeenCalled();
  });

  it("có token thì gọi /me và set admin profile", async () => {
    sessionStorage.setItem("admin_access_token", "admin-tok");
    mockedApi.me.mockResolvedValue({
      success: true,
      data: adminProfile,
    } satisfies APIResponse<AdminInfo>);

    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
    });
    expect(screen.getByTestId("name")).toHaveTextContent("Admin Test");
    expect(screen.getByTestId("system-admin")).toHaveTextContent("true");
  });

  it("token hết hạn (me thất bại) thì xóa token và set unauthenticated", async () => {
    sessionStorage.setItem("admin_access_token", "expired-tok");
    mockedApi.me.mockRejectedValue(new Error("Unauthorized"));

    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
    expect(sessionStorage.getItem("admin_access_token")).toBeNull();
  });

  it("login lưu token và set admin profile", async () => {
    mockedApi.login.mockResolvedValue({
      success: true,
      data: { access_token: "new-admin-tok", admin: adminProfile },
    });

    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    await act(async () => {
      screen.getByText("login").click();
    });

    await waitFor(() => {
      expect(sessionStorage.getItem("admin_access_token")).toBe(
        "new-admin-tok",
      );
      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
      expect(screen.getByTestId("name")).toHaveTextContent("Admin Test");
    });
  });

  it("logout xóa token dù API lỗi", async () => {
    sessionStorage.setItem("admin_access_token", "admin-tok");
    mockedApi.me.mockResolvedValue({
      success: true,
      data: adminProfile,
    } satisfies APIResponse<AdminInfo>);
    mockedApi.logout.mockRejectedValue(new Error("network"));

    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
    });

    await act(async () => {
      screen.getByText("logout").click();
    });

    await waitFor(() => {
      expect(sessionStorage.getItem("admin_access_token")).toBeNull();
      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
      expect(screen.getByTestId("name")).toHaveTextContent("");
    });
  });

  it("login không lưu token nếu API trả success: false", async () => {
    mockedApi.login.mockResolvedValue({
      success: false,
      data: { access_token: "", admin: adminProfile },
      error: { code: "AUTH_FAILED", message: "Sai mật khẩu", details: [] },
    });

    render(
      <AdminAuthProvider>
        <Probe />
      </AdminAuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    await act(async () => {
      screen.getByText("login").click();
    });

    expect(sessionStorage.getItem("admin_access_token")).toBeNull();
    expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
  });
});
