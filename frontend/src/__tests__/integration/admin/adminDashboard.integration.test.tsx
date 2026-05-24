import { screen, waitFor } from "@testing-library/react";
import { installFetchMock, jsonOk } from "../helpers/fetchMock";
import { renderAdminApp } from "../helpers/renderAdminApp";
import { adminProfile, dashboardStats } from "../helpers/adminFixtures";

describe("integration: admin dashboard", () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem("admin_access_token", "admin-token-123");
  });

  it("hiển thị 3 chỉ số thống kê", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/dashboard/stats")) {
        return jsonOk(dashboardStats);
      }
      return null;
    });

    renderAdminApp(["/admin"]);

    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(await screen.findByText("5")).toBeInTheDocument();
    expect(await screen.findByText("3")).toBeInTheDocument();
    expect(await screen.findByText("12")).toBeInTheDocument();
  });

  it("hiển thị nhãn mô tả cho từng thẻ thống kê", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/dashboard/stats")) {
        return jsonOk(dashboardStats);
      }
      return null;
    });

    renderAdminApp(["/admin"]);

    expect(await screen.findByText(/Báo cáo mới/)).toBeInTheDocument();
    expect(await screen.findByText(/SV chưa kích hoạt/)).toBeInTheDocument();
    expect(await screen.findByText(/Địa điểm mới/)).toBeInTheDocument();
  });

  it("chuyển hướng về login nếu chưa đăng nhập", async () => {
    sessionStorage.removeItem("admin_access_token");

    installFetchMock(() => null);

    renderAdminApp(["/admin"]);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Quản Trị" }),
      ).toBeInTheDocument();
    });
  });
});
