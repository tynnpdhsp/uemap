import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResetPasswordPage from "../../pages/student/ResetPasswordPage";
import { api } from "../../api/client";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/client", () => ({
  api: { post: jest.fn() },
}));

const mockedPost = api.post as jest.Mock;

describe("ResetPasswordPage", () => {
  const email = "4901104172@student.hcmue.edu.vn";
  const token = "reset-token";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("báo lỗi khi thiếu token trên URL", () => {
    renderWithRouter(<ResetPasswordPage />, {
      route: `/forgot-password/reset?email=${encodeURIComponent(email)}`,
      routes: [
        { path: "/forgot-password/reset", element: <ResetPasswordPage /> },
      ],
    });

    expect(
      screen.getByText(/không hợp lệ hoặc thiếu thông tin/i),
    ).toBeInTheDocument();
  });

  it("từ chối mật khẩu xác nhận không khớp", async () => {
    const user = userEvent.setup();
    renderWithRouter(<ResetPasswordPage />, {
      route: `/forgot-password/reset?email=${encodeURIComponent(email)}&token=${token}`,
      routes: [
        { path: "/forgot-password/reset", element: <ResetPasswordPage /> },
      ],
    });

    await user.type(
      screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
      "newpassword123",
    );
    await user.type(
      screen.getByPlaceholderText("Nhập lại mật khẩu mới"),
      "different12345",
    );
    await user.click(screen.getByRole("button", { name: /Đặt Lại Mật Khẩu/i }));

    expect(await screen.findByText(/không khớp/)).toBeInTheDocument();
  });

  it("đặt lại mật khẩu thành công", async () => {
    const user = userEvent.setup();
    mockedPost.mockResolvedValue({ success: true, data: {} });

    renderWithRouter(<ResetPasswordPage />, {
      route: `/forgot-password/reset?email=${encodeURIComponent(email)}&token=${token}`,
      routes: [
        { path: "/forgot-password/reset", element: <ResetPasswordPage /> },
      ],
    });

    const pwd = "newsecurepassword123";
    await user.type(screen.getByPlaceholderText("Tối thiểu 8 ký tự"), pwd);
    await user.type(screen.getByPlaceholderText("Nhập lại mật khẩu mới"), pwd);
    await user.click(screen.getByRole("button", { name: /Đặt Lại Mật Khẩu/i }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/forgot-password/reset", {
        email,
        reset_token: token,
        password: pwd,
      });
      expect(
        screen.getByText(/Đặt lại mật khẩu thành công/),
      ).toBeInTheDocument();
    });
  });
});
