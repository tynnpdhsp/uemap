import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk, jsonError } from "../helpers/fetchMock";
import { renderAdminApp } from "../helpers/renderAdminApp";
import {
  ADMIN_USERNAME,
  ADMIN_PASSWORD,
  ADMIN_DISPLAY_NAME,
  adminProfile,
  dashboardStats,
} from "../helpers/adminFixtures";

describe("integration: đăng nhập admin", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("đăng nhập thành công chuyển sang dashboard", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (method === "POST" && url.includes("/api/admin/auth/login")) {
        return jsonOk({ access_token: "admin-token-123", admin: adminProfile });
      }
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/dashboard/stats")) {
        return jsonOk(dashboardStats);
      }
      return null;
    });

    renderAdminApp(["/admin/login"]);

    expect(
      screen.getByRole("heading", { name: "Quản Trị" }),
    ).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("admin"), ADMIN_USERNAME);
    await user.type(screen.getByPlaceholderText("••••••••"), ADMIN_PASSWORD);
    fireEvent.submit(
      screen.getByRole("button", { name: "Đăng Nhập" }).closest("form")!,
    );

    await waitFor(() => {
      expect(sessionStorage.getItem("admin_access_token")).toBe(
        "admin-token-123",
      );
    });
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
  });

  it("đăng nhập thất bại hiển thị lỗi", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (method === "POST" && url.includes("/api/admin/auth/login")) {
        return jsonError("Sai tên đăng nhập hoặc mật khẩu.", 401);
      }
      return null;
    });

    renderAdminApp(["/admin/login"]);

    await user.type(screen.getByPlaceholderText("admin"), "wrong");
    await user.type(screen.getByPlaceholderText("••••••••"), "wrong");
    fireEvent.submit(
      screen.getByRole("button", { name: "Đăng Nhập" }).closest("form")!,
    );

    expect(
      await screen.findByText(/Sai tên đăng nhập hoặc mật khẩu/),
    ).toBeInTheDocument();
    expect(sessionStorage.getItem("admin_access_token")).toBeNull();
  });

  it("đăng xuất xóa token và chuyển về trang login", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem("admin_access_token", "admin-token-123");

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/dashboard/stats")) {
        return jsonOk(dashboardStats);
      }
      if (method === "POST" && url.includes("/api/admin/auth/logout")) {
        return jsonOk(null);
      }
      return null;
    });

    renderAdminApp(["/admin"]);

    const matches = await screen.findAllByText(ADMIN_DISPLAY_NAME);
    expect(matches.length).toBeGreaterThanOrEqual(1);

    const logoutButtons = screen.getAllByRole("button", { name: /Đăng xuất/i });
    await user.click(logoutButtons[0]);

    await waitFor(() => {
      expect(sessionStorage.getItem("admin_access_token")).toBeNull();
    });
  });
});
