import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HomePage from "../../pages/public/HomePage";
import { useAuth } from "../../context/AuthContext";

jest.mock("../../context/AuthContext", () => ({
  useAuth: jest.fn(),
}));

jest.mock("../../api/map", () => ({
  mapApi: {
    getConfig: jest.fn().mockResolvedValue({
      success: true,
      data: {
        default_center: { lat: 10.7628, lng: 106.6824 },
        default_zoom: 16,
        geofence: null,
      },
    }),
    getCategories: jest.fn().mockResolvedValue({
      success: true,
      data: [
        { id: "cat1", name: "Quán ăn", color: "#ff0000" },
      ],
    }),
  },
}));

jest.mock("../../api/places", () => ({
  placesApi: {
    getMarkers: jest.fn().mockResolvedValue({
      success: true,
      data: [],
    }),
  },
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

    expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument();
    expect(screen.getByText(/Sinh viên:/i)).toBeInTheDocument();
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
      screen.getByText(/Đăng nhập để đóng góp vị trí/i),
    ).toBeInTheDocument();
  });
});
