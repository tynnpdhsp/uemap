import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import StudentLayout from "../../layouts/StudentLayout";
import { useAuth } from "../../context/AuthContext";

const mockLogout = jest.fn();
const mockNavigate = jest.fn();

jest.mock("../../context/AuthContext", () => ({
  useAuth: jest.fn(),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockedUseAuth = useAuth as jest.Mock;

describe("StudentLayout", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogout.mockResolvedValue(undefined);
  });

  it("hiển thị nút đăng nhập khi chưa xác thực", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: false,
      student: null,
      logout: mockLogout,
    });

    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<StudentLayout />}>
            <Route index element={<div>child</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Đăng Nhập" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Đăng Ký" })).toBeInTheDocument();
  });

  it("đăng xuất khi bấm nút", async () => {
    const user = userEvent.setup();
    mockedUseAuth.mockReturnValue({
      isAuthenticated: true,
      student: { full_name: "Nguyễn Văn A" },
      logout: mockLogout,
    });

    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<StudentLayout />}>
            <Route index element={<div>child</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Đăng Xuất" }));

    expect(mockLogout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });
});
