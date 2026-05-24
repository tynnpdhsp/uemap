import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AdminProtectedRoute from "../../components/AdminProtectedRoute";
import { useAdminAuth } from "../../context/AdminAuthContext";

jest.mock("../../context/AdminAuthContext", () => ({
  useAdminAuth: jest.fn(),
}));

const mockedUseAdminAuth = useAdminAuth as jest.Mock;

describe("AdminProtectedRoute", () => {
  it("hiển thị loading spinner khi đang tải", () => {
    mockedUseAdminAuth.mockReturnValue({
      isAuthenticated: false,
      loading: true,
    });

    const { container } = render(
      <MemoryRouter>
        <AdminProtectedRoute>
          <div>admin secret</div>
        </AdminProtectedRoute>
      </MemoryRouter>,
    );

    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
    expect(screen.queryByText("admin secret")).not.toBeInTheDocument();
  });

  it("chuyển /admin/login khi chưa đăng nhập", () => {
    mockedUseAdminAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
    });

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminProtectedRoute>
          <div>admin secret</div>
        </AdminProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.queryByText("admin secret")).not.toBeInTheDocument();
  });

  it("render children khi đã đăng nhập admin", () => {
    mockedUseAdminAuth.mockReturnValue({
      isAuthenticated: true,
      loading: false,
    });

    render(
      <MemoryRouter>
        <AdminProtectedRoute>
          <div>admin secret</div>
        </AdminProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.getByText("admin secret")).toBeInTheDocument();
  });

  it("không cho phép truy cập khi token hết hạn (isAuthenticated = false)", () => {
    mockedUseAdminAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
    });

    render(
      <MemoryRouter initialEntries={["/admin/categories"]}>
        <AdminProtectedRoute>
          <div>categories page</div>
        </AdminProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.queryByText("categories page")).not.toBeInTheDocument();
  });
});
