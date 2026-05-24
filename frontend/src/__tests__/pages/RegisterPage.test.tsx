import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import RegisterPage from "../../pages/student/RegisterPage";
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

const valid = {
  email: "4901104172@student.hcmue.edu.vn",
  password: "testpassword123",
  fullName: "Nguyễn Văn A",
};

async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(
    screen.getByPlaceholderText("4901104172@student.hcmue.edu.vn"),
    valid.email,
  );
  await user.type(
    screen.getByPlaceholderText("e.g. Nguyễn Văn A"),
    valid.fullName,
  );
  await user.type(
    screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
    valid.password,
  );
  await user.type(
    screen.getByPlaceholderText("Nhập lại mật khẩu"),
    valid.password,
  );
  await user.click(screen.getByRole("checkbox"));
}

describe("RegisterPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("từ chối email sai định dạng", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    await user.type(
      screen.getByPlaceholderText("4901104172@student.hcmue.edu.vn"),
      "bad@gmail.com",
    );
    await user.type(
      screen.getByPlaceholderText("e.g. Nguyễn Văn A"),
      valid.fullName,
    );
    await user.type(
      screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
      valid.password,
    );
    await user.type(
      screen.getByPlaceholderText("Nhập lại mật khẩu"),
      valid.password,
    );
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Đăng Ký" }));

    expect(await screen.findByText(/10 chữ số/)).toBeInTheDocument();
    expect(mockedPost).not.toHaveBeenCalled();
  });

  it("từ chối mật khẩu xác nhận không khớp", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    await user.type(
      screen.getByPlaceholderText("4901104172@student.hcmue.edu.vn"),
      valid.email,
    );
    await user.type(
      screen.getByPlaceholderText("e.g. Nguyễn Văn A"),
      valid.fullName,
    );
    await user.type(
      screen.getByPlaceholderText("Tối thiểu 8 ký tự"),
      valid.password,
    );
    await user.type(
      screen.getByPlaceholderText("Nhập lại mật khẩu"),
      "otherpassword1",
    );
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Đăng Ký" }));

    expect(await screen.findByText(/không khớp/)).toBeInTheDocument();
  });

  it("đăng ký thành công chuyển verify OTP", async () => {
    const user = userEvent.setup();
    mockedPost.mockResolvedValue({ success: true, data: {} });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Đăng Ký" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/auth/register", {
        email: valid.email,
        password: valid.password,
        password_confirm: valid.password,
        full_name: valid.fullName,
        accept_terms: true,
      });
      expect(mockNavigate).toHaveBeenCalledWith(
        `/register/verify-otp?email=${encodeURIComponent(valid.email)}`,
      );
    });
  });
});
