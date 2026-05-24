import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProfilePage from "../../pages/student/ProfilePage";
import { api } from "../../api/client";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/client", () => ({
  api: {
    get: jest.fn(),
    patch: jest.fn(),
    post: jest.fn(),
  },
}));

jest.mock("../../context/AuthContext", () => ({
  useAuth: () => ({ logout: jest.fn() }),
}));

const mockedGet = api.get as jest.Mock;
const mockedPatch = api.patch as jest.Mock;
const mockedPost = api.post as jest.Mock;

const profile = {
  email: "4901104172@student.hcmue.edu.vn",
  full_name: "Nguyễn Văn A",
  status: "active",
  status_label: "Đã kích hoạt",
  activated_at_display: "01/01/2025 10:00",
  locked_reason: null,
};

describe("ProfilePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGet.mockResolvedValue({ success: true, data: profile });
  });

  it("hiển thị thông tin sau khi tải", async () => {
    renderWithRouter(<ProfilePage />);

    expect(await screen.findByText(profile.email)).toBeInTheDocument();
    expect(screen.getByText(profile.status_label)).toBeInTheDocument();
  });

  it("cập nhật họ tên thành công", async () => {
    const user = userEvent.setup();
    mockedPatch.mockResolvedValue({
      success: true,
      data: { ...profile, full_name: "Nguyễn Văn B" },
    });

    renderWithRouter(<ProfilePage />);
    await screen.findByText(profile.email);

    const nameInput = screen.getByDisplayValue(profile.full_name);
    await user.clear(nameInput);
    await user.type(nameInput, "Nguyễn Văn B");
    await user.click(
      screen.getByRole("button", { name: /Cập Nhật Thông Tin/i }),
    );

    await waitFor(() => {
      expect(mockedPatch).toHaveBeenCalledWith("/me", {
        full_name: "Nguyễn Văn B",
      });
      expect(
        screen.getByText(/Cập nhật thông tin cá nhân thành công/),
      ).toBeInTheDocument();
    });
  });

  it("đổi mật khẩu thành công", async () => {
    const user = userEvent.setup();
    mockedPost.mockResolvedValue({ success: true, data: {} });

    renderWithRouter(<ProfilePage />);
    await screen.findByText(profile.email);

    await user.type(screen.getByPlaceholderText("••••••••"), "oldpassword123");
    await user.type(
      screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
      "newpassword123",
    );
    await user.type(
      screen.getByPlaceholderText("Nhập lại mật khẩu mới"),
      "newpassword123",
    );
    await user.click(
      screen.getByRole("button", { name: /Thay Đổi Mật Khẩu/i }),
    );

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/me/change-password", {
        current_password: "oldpassword123",
        password: "newpassword123",
        password_confirm: "newpassword123",
      });
      expect(screen.getByText(/Đổi mật khẩu thành công/)).toBeInTheDocument();
    });
  });

  it("từ chối họ tên quá ngắn", async () => {
    const user = userEvent.setup();
    renderWithRouter(<ProfilePage />);
    await screen.findByText(profile.email);

    const nameInput = screen.getByDisplayValue(profile.full_name);
    await user.clear(nameInput);
    await user.type(nameInput, "ABC");
    await user.click(
      screen.getByRole("button", { name: /Cập Nhật Thông Tin/i }),
    );

    expect(await screen.findByText(/5 đến 100 ký tự/)).toBeInTheDocument();
    expect(mockedPatch).not.toHaveBeenCalled();
  });
});
