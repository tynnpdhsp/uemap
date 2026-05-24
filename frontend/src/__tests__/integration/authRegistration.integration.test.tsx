import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  TEST_EMAIL,
  TEST_NAME,
  TEST_OTP,
  TEST_PASSWORD,
  registerSuccessBody,
} from "./helpers/fixtures";

describe("integration: đăng ký và kích hoạt OTP", () => {
  beforeEach(() => {
    sessionStorage.clear();
    installFetchMock((url, method, body) => {
      if (method === "POST" && url.includes("/api/auth/register")) {
        return jsonOk(registerSuccessBody);
      }
      if (method === "POST" && url.includes("/api/auth/otp/verify")) {
        expect(body).toEqual({
          email: TEST_EMAIL,
          otp: TEST_OTP,
          purpose: "activation",
        });
        return jsonOk({ activated_at_display: "01/01/2025 10:00" });
      }
      return null;
    });
  });

  it("luồng đăng ký → xác thực OTP thành công", async () => {
    const user = userEvent.setup();
    renderApp(["/register"]);

    await user.type(
      screen.getByPlaceholderText("4901104172@student.hcmue.edu.vn"),
      TEST_EMAIL,
    );
    await user.type(screen.getByPlaceholderText("e.g. Nguyễn Văn A"), TEST_NAME);
    await user.type(screen.getByPlaceholderText("Tối thiểu 8 ký tự"), TEST_PASSWORD);
    await user.type(screen.getByPlaceholderText("Nhập lại mật khẩu"), TEST_PASSWORD);
    await user.click(screen.getByRole("checkbox"));

    const form = screen.getByRole("button", { name: "Đăng Ký" }).closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    expect(
      await screen.findByRole("heading", { name: /Xác Thực OTP/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(TEST_EMAIL)).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("000000"), TEST_OTP);
    fireEvent.submit(
      screen.getByRole("button", { name: /Kích Hoạt Tài Khoản/i }).closest("form")!,
    );

    expect(
      await screen.findByText(/Kích hoạt tài khoản thành công/i),
    ).toBeInTheDocument();
  });
});
