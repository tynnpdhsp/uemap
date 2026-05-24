import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ForgotPasswordPage from "../../pages/student/ForgotPasswordPage";
import { api } from "../../api/client";

jest.mock("../../api/client", () => ({
  api: { post: jest.fn() },
}));

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockedPost = api.post as jest.Mock;

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("từ chối email không hợp lệ", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    );

    await user.type(
      screen.getByPlaceholderText(/4901104172/),
      "invalid@mail.com",
    );
    await user.click(screen.getByRole("button", { name: "Gửi Mã OTP" }));

    expect(await screen.findByText(/10 chữ số/)).toBeInTheDocument();
    expect(mockedPost).not.toHaveBeenCalled();
  });

  it("gửi OTP quên mật khẩu thành công", async () => {
    const user = userEvent.setup();
    const email = "4901104172@student.hcmue.edu.vn";
    mockedPost.mockResolvedValue({ success: true, data: {} });

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByPlaceholderText(/4901104172/), email);
    await user.click(screen.getByRole("button", { name: "Gửi Mã OTP" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/forgot-password", {
        email,
      });
      expect(mockNavigate).toHaveBeenCalledWith(
        `/forgot-password/verify-otp?email=${encodeURIComponent(email)}`,
      );
    });
  });
});
