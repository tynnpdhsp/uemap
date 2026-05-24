import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../../context/AuthContext";
import { api } from "../../api/client";

jest.mock("../../api/client", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;

function Probe() {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(auth.loading)}</span>
      <span data-testid="authenticated">{String(auth.isAuthenticated)}</span>
      <span data-testid="name">{auth.student?.full_name ?? ""}</span>
      <button
        type="button"
        onClick={() => auth.login("e@student.hcmue.edu.vn", "pass")}
      >
        login
      </button>
      <button type="button" onClick={() => auth.logout()}>
        logout
      </button>
      <button type="button" onClick={() => auth.updateProfile("Tên Mới")}>
        update
      </button>
    </div>
  );
}

const profile = {
  email: "4901104172@student.hcmue.edu.vn",
  full_name: "Nguyễn Văn A",
  status: "active",
  status_label: "Đã kích hoạt",
  activated_at_display: "01/01/2025 10:00",
  locked_reason: null,
};

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
  });

  it("useAuth ngoài Provider ném lỗi", () => {
    const Bad = () => {
      useAuth();
      return null;
    };
    expect(() => render(<Bad />)).toThrow(
      "useAuth phải được sử dụng trong một AuthProvider",
    );
  });

  it("không có token thì không đăng nhập", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
    expect(mockedApi.get).not.toHaveBeenCalled();
  });

  it("có token thì tải profile", async () => {
    sessionStorage.setItem("sv_access_token", "tok");
    mockedApi.get.mockResolvedValue({ success: true, data: profile });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
    });
    expect(screen.getByTestId("name")).toHaveTextContent("Nguyễn Văn A");
  });

  it("login lưu token và tải profile", async () => {
    mockedApi.post.mockResolvedValue({
      success: true,
      data: { access_token: "new-tok" },
    });
    mockedApi.get.mockResolvedValue({ success: true, data: profile });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => screen.getByTestId("loading").textContent === "false");

    await act(async () => {
      screen.getByText("login").click();
    });

    await waitFor(() => {
      expect(sessionStorage.getItem("sv_access_token")).toBe("new-tok");
      expect(screen.getByTestId("name")).toHaveTextContent("Nguyễn Văn A");
    });
  });

  it("logout xóa token dù API lỗi", async () => {
    sessionStorage.setItem("sv_access_token", "tok");
    mockedApi.get.mockResolvedValue({ success: true, data: profile });
    mockedApi.post.mockRejectedValue(new Error("network"));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(
      () => screen.getByTestId("authenticated").textContent === "true",
    );

    await act(async () => {
      screen.getByText("logout").click();
    });

    await waitFor(() => {
      expect(sessionStorage.getItem("sv_access_token")).toBeNull();
      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
    });
  });

  it("updateProfile cập nhật student", async () => {
    sessionStorage.setItem("sv_access_token", "tok");
    mockedApi.get.mockResolvedValue({ success: true, data: profile });
    mockedApi.patch.mockResolvedValue({
      success: true,
      data: { ...profile, full_name: "Tên Mới" },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(
      () => screen.getByTestId("authenticated").textContent === "true",
    );

    await act(async () => {
      screen.getByText("update").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("name")).toHaveTextContent("Tên Mới");
    });
  });
});
