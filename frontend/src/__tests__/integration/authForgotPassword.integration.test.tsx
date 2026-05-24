import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  TEST_EMAIL,
  TEST_NEW_PASSWORD,
  TEST_OTP,
  TEST_RESET_TOKEN,
} from "./helpers/fixtures";

describe("integration: quên mật khẩu", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("luồng quên MK → OTP → đặt lại mật khẩu", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method, body) => {
      if (method === "POST" && url.includes("/api/auth/forgot-password") && !url.includes("verify") && !url.includes("reset")) {
        return jsonOk({ message: "ok" });
      }
      if (method === "POST" && url.includes("/api/auth/forgot-password/verify")) {
        return jsonOk({ reset_token: TEST_RESET_TOKEN });
      }
      if (method === "POST" && url.includes("/api/auth/otp/resend")) {
        expect(body).toMatchObject({
          email: TEST_EMAIL,
          purpose: "password_reset",
        });
        return jsonOk({ otp_resend_available_at: "2025-01-01T00:00:00.000Z" });
      }
      if (method === "POST" && url.includes("/api/auth/forgot-password/reset")) {
        expect(body).toMatchObject({
          email: TEST_EMAIL,
          reset_token: TEST_RESET_TOKEN,
          password: TEST_NEW_PASSWORD,
        });
        return jsonOk({ message: "Đặt lại mật khẩu thành công." });
      }
      return null;
    });

    renderApp(["/forgot-password"]);

    await user.type(screen.getByPlaceholderText(/4901104172/), TEST_EMAIL);
    fireEvent.submit(
      screen.getByRole("button", { name: "Gửi Mã OTP" }).closest("form")!,
    );

    expect(
      await screen.findByRole("heading", { name: /Xác Thực OTP Quên Mật Khẩu/i }),
    ).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("000000"), TEST_OTP);
    fireEvent.submit(
      screen.getByRole("button", { name: /Xác Thực Mã OTP/i }).closest("form")!,
    );

    await waitFor(
      () => {
        expect(
          screen.getByRole("heading", { name: /Đặt Lại Mật Khẩu/i }),
        ).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    await user.type(screen.getByPlaceholderText("Tối thiểu 8 ký tự"), TEST_NEW_PASSWORD);
    await user.type(screen.getByPlaceholderText("Nhập lại mật khẩu mới"), TEST_NEW_PASSWORD);
    fireEvent.submit(
      screen.getByRole("button", { name: /Đặt Lại Mật Khẩu/i }).closest("form")!,
    );

    expect(
      await screen.findByText(/Đặt lại mật khẩu thành công/i),
    ).toBeInTheDocument();
  });
});
