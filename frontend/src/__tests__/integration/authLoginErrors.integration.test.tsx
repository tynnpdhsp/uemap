import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonError } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import { TEST_EMAIL, TEST_PASSWORD } from "./helpers/fixtures";

describe("integration: lỗi đăng nhập", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("hiển thị lỗi và link kích hoạt khi tài khoản chưa kích hoạt", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (method === "POST" && url.includes("/api/auth/login")) {
        return jsonError(
          "Tài khoản chưa được kích hoạt. Vui lòng nhập mã OTP để kích hoạt.",
          401,
        );
      }
      return null;
    });

    renderApp(["/login"]);

    await user.type(screen.getByPlaceholderText(/4901104172/), TEST_EMAIL);
    await user.type(screen.getByPlaceholderText("••••••••"), TEST_PASSWORD);
    fireEvent.submit(
      screen.getByRole("button", { name: "Đăng Nhập" }).closest("form")!,
    );

    expect(
      await screen.findByText(/chưa được kích hoạt/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /kích hoạt tài khoản/i }),
    ).toHaveAttribute(
      "href",
      `/register/verify-otp?email=${encodeURIComponent(TEST_EMAIL)}`,
    );
  });
});
