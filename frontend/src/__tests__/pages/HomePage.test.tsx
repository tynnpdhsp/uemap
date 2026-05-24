import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HomePage from "../../pages/public/HomePage";
import { useAuth } from "../../context/AuthContext";

jest.mock("../../context/AuthContext", () => ({
  useAuth: jest.fn(),
}));

const mockedUseAuth = useAuth as jest.Mock;

describe("HomePage", () => {
  it("hiển thị lời chào khi đã đăng nhập", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: true,
      student: { full_name: "Nguyễn Văn A" },
    });

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(
      screen.getByText(/Chào mừng quay trở lại, Nguyễn Văn A!/),
    ).toBeInTheDocument();
  });

  it("gợi ý đăng nhập khi chưa đăng nhập", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: false,
      student: null,
    });

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(
      screen.getByText(/Đăng nhập để cập nhật vị trí/),
    ).toBeInTheDocument();
  });
});
