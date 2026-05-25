import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  TEST_EMAIL,
  TEST_NAME,
  TEST_NEW_PASSWORD,
  TEST_PASSWORD,
  activeProfile,
} from "./helpers/fixtures";

describe("integration: trang cá nhân", () => {
  beforeEach(() => {
    sessionStorage.setItem("sv_access_token", "profile-token");
  });

  it("tải hồ sơ, cập nhật tên và đổi mật khẩu", async () => {
    const user = userEvent.setup();
    const updatedName = "Nguyễn Văn Integration";

    installFetchMock((url, method, body) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "PATCH" && url.includes("/api/me")) {
        expect(body).toEqual({ full_name: updatedName });
        return jsonOk({ ...activeProfile, full_name: updatedName });
      }
      if (method === "POST" && url.includes("/api/me/change-password")) {
        expect(body).toEqual({
          current_password: TEST_PASSWORD,
          password: TEST_NEW_PASSWORD,
          password_confirm: TEST_NEW_PASSWORD,
        });
        return jsonOk({ message: "Đổi mật khẩu thành công." });
      }
      return null;
    });

    renderApp(["/profile"]);

    expect(await screen.findByText(TEST_EMAIL)).toBeInTheDocument();
    expect(screen.getByText(activeProfile.status_label)).toBeInTheDocument();

    const nameInput = screen.getByDisplayValue(TEST_NAME);
    await user.clear(nameInput);
    await user.type(nameInput, updatedName);
    await user.click(
      screen.getByRole("button", { name: /Cập Nhật Thông Tin/i }),
    );

    expect(
      await screen.findByText(/Cập nhật thông tin cá nhân thành công/i),
    ).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("••••••••"), TEST_PASSWORD);
    await user.type(
      screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
      TEST_NEW_PASSWORD,
    );
    await user.type(
      screen.getByPlaceholderText("Nhập lại mật khẩu mới"),
      TEST_NEW_PASSWORD,
    );
    await user.click(
      screen.getByRole("button", { name: /Thay Đổi Mật Khẩu/i }),
    );

    expect(
      await screen.findByText(/Đổi mật khẩu thành công/i),
    ).toBeInTheDocument();
  });

  it("khởi tạo auth từ sessionStorage và vào /profile", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      return null;
    });

    const { router } = renderApp(["/profile"]);

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/profile");
    });
    expect(await screen.findByText(TEST_EMAIL)).toBeInTheDocument();
  });
});
