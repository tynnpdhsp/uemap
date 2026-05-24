import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "../../pages/student/LoginPage";

const mockLogin = jest.fn();
const mockNavigate = jest.fn();

jest.mock("../../context/AuthContext", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("đăng nhập thành công chuyển trang chủ", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue({ success: true });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(
      screen.getByPlaceholderText(/4901104172/),
      "4901104172@student.hcmue.edu.vn",
    );
    await user.type(screen.getByPlaceholderText("••••••••"), "testpassword123");
    await user.click(screen.getByRole("button", { name: "Đăng Nhập" }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        "4901104172@student.hcmue.edu.vn",
        "testpassword123",
      );
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("hiển thị lỗi và link kích hoạt khi chưa kích hoạt", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(
      new Error("Tài khoản chưa được kích hoạt. Vui lòng nhập OTP"),
    );

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(
      screen.getByPlaceholderText(/4901104172/),
      "4901104172@student.hcmue.edu.vn",
    );
    await user.type(screen.getByPlaceholderText("••••••••"), "testpassword123");
    await user.click(screen.getByRole("button", { name: "Đăng Nhập" }));

    await waitFor(() => {
      expect(screen.getByText(/chưa được kích hoạt/i)).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /kích hoạt tài khoản/i }),
      ).toHaveAttribute(
        "href",
        "/register/verify-otp?email=4901104172%40student.hcmue.edu.vn",
      );
    });
  });
});
