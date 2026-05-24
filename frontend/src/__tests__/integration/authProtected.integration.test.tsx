import { screen } from "@testing-library/react";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";

describe("integration: route bảo vệ", () => {
  beforeEach(() => {
    sessionStorage.clear();
    installFetchMock((url) => {
      if (url.includes("/api/config/map")) {
        return jsonOk({
          default_center: { lat: 10.7628, lng: 106.6824 },
          default_zoom: 16,
          geofence: null,
        });
      }
      if (url.includes("/api/categories")) {
        return jsonOk([]);
      }
      if (url.includes("/api/places/markers")) {
        return jsonOk([]);
      }
      return null;
    });
  });

  it("chưa đăng nhập truy cập /profile chuyển về /login", async () => {
    renderApp(["/profile"]);

    expect(
      await screen.findByRole("heading", { name: "Đăng Nhập" }),
    ).toBeInTheDocument();
  });

  it("trang chủ khi chưa đăng nhập hiển thị liên kết đăng nhập", () => {
    renderApp(["/"]);

    expect(screen.getByRole("link", { name: "Đăng Nhập" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Đăng Ký" })).toBeInTheDocument();
  });
});
