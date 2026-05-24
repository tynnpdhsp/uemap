import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ForgotVerifyOtpPage from "../../pages/student/ForgotVerifyOtpPage";
import { api } from "../../api/client";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/client", () => ({
  api: { post: jest.fn() },
}));

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockedPost = api.post as jest.Mock;

describe("ForgotVerifyOtpPage", () => {
  const email = "4901104172@student.hcmue.edu.vn";

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("xác thực OTP và chuyển trang reset", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    mockedPost.mockResolvedValue({
      success: true,
      data: { reset_token: "reset-tok-xyz" },
    });

    renderWithRouter(<ForgotVerifyOtpPage />, {
      route: `/forgot-password/verify-otp?email=${encodeURIComponent(email)}`,
      routes: [
        {
          path: "/forgot-password/verify-otp",
          element: <ForgotVerifyOtpPage />,
        },
      ],
    });

    await user.type(screen.getByPlaceholderText("000000"), "111111");
    await user.click(screen.getByRole("button", { name: /Xác Thực Mã OTP/i }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/forgot-password/verify", {
        email,
        otp: "111111",
      });
    });

    jest.advanceTimersByTime(1500);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        `/forgot-password/reset?email=${encodeURIComponent(email)}&token=${encodeURIComponent("reset-tok-xyz")}`,
      );
    });
  });
});
