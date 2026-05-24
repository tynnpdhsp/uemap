import { screen } from "@testing-library/react";
import { installFetchMock } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";

describe("integration: route bảo vệ", () => {
  beforeEach(() => {
    sessionStorage.clear();
    installFetchMock(() => null);
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
