import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import VerifyOtpPage from "../../pages/student/VerifyOtpPage";
import { api } from "../../api/client";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/client", () => ({
  api: { post: jest.fn() },
}));

const mockedPost = api.post as jest.Mock;

describe("VerifyOtpPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("báo lỗi khi thiếu email trên URL", () => {
    renderWithRouter(<VerifyOtpPage />, {
      route: "/register/verify-otp",
      routes: [{ path: "/register/verify-otp", element: <VerifyOtpPage /> }],
    });

    expect(
      screen.getByText(/Không tìm thấy thông tin email/),
    ).toBeInTheDocument();
  });

  it("từ chối OTP không đủ 6 số", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    renderWithRouter(<VerifyOtpPage />, {
      route: "/register/verify-otp?email=4901104172@student.hcmue.edu.vn",
      routes: [{ path: "/register/verify-otp", element: <VerifyOtpPage /> }],
    });

    await user.type(screen.getByPlaceholderText("000000"), "123");
    await user.click(screen.getByRole("button", { name: /Kích Hoạt/i }));

    expect(await screen.findByText(/6 chữ số/)).toBeInTheDocument();
    expect(mockedPost).not.toHaveBeenCalled();
  });

  it("xác thực OTP thành công", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    mockedPost.mockResolvedValue({ success: true, data: {} });

    renderWithRouter(<VerifyOtpPage />, {
      route: "/register/verify-otp?email=4901104172@student.hcmue.edu.vn",
      routes: [{ path: "/register/verify-otp", element: <VerifyOtpPage /> }],
    });

    await user.type(screen.getByPlaceholderText("000000"), "111111");
    await user.click(screen.getByRole("button", { name: /Kích Hoạt/i }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/otp/verify", {
        email: "4901104172@student.hcmue.edu.vn",
        otp: "111111",
        purpose: "activation",
      });
      expect(
        screen.getByText(/Kích hoạt tài khoản thành công/),
      ).toBeInTheDocument();
    });
  });

  it("gửi lại OTP kích hoạt", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    mockedPost.mockResolvedValue({ success: true, data: {} });

    renderWithRouter(<VerifyOtpPage />, {
      route: "/register/verify-otp?email=4901104172@student.hcmue.edu.vn",
      routes: [{ path: "/register/verify-otp", element: <VerifyOtpPage /> }],
    });

    await user.click(screen.getByRole("button", { name: /Gửi lại mã OTP/i }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/otp/resend", {
        email: "4901104172@student.hcmue.edu.vn",
        purpose: "activation",
      });
    });
  });
});
