import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  TEST_EMAIL,
  TEST_NAME,
  TEST_PASSWORD,
  activeProfile,
} from "./helpers/fixtures";

describe("integration: đăng nhập và đăng xuất", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("đăng nhập thành công hiển thị lời chào trên trang chủ", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (method === "POST" && url.includes("/api/auth/login")) {
        return jsonOk({ access_token: "integration-token" });
      }
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk({
          default_center: { lat: 10.7628, lng: 106.6824 },
          default_zoom: 16,
          geofence: null,
        });
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk([]);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk([]);
      }
      return null;
    });

    renderApp(["/login"]);

    await user.type(screen.getByPlaceholderText(/4901104172/), TEST_EMAIL);
    await user.type(screen.getByPlaceholderText("••••••••"), TEST_PASSWORD);
    fireEvent.submit(
      screen.getByRole("button", { name: "Đăng Nhập" }).closest("form")!,
    );

    await waitFor(() => {
      expect(sessionStorage.getItem("sv_access_token")).toBe(
        "integration-token",
      );
    });
    expect(await screen.findByText(TEST_NAME)).toBeInTheDocument();
    expect(await screen.findByText(/Sinh viên:/i)).toBeInTheDocument();
  });

  it("đăng xuất từ layout chuyển về trang login", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem("sv_access_token", "integration-token");

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "POST" && url.includes("/api/auth/logout")) {
        return jsonOk(null);
      }
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk({
          default_center: { lat: 10.7628, lng: 106.6824 },
          default_zoom: 16,
          geofence: null,
        });
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk([]);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk([]);
      }
      return null;
    });

    renderApp(["/"]);

    expect(await screen.findByText(TEST_NAME)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Đăng Xuất" }));

    expect(
      await screen.findByRole("heading", { name: "Đăng Nhập" }),
    ).toBeInTheDocument();
    expect(sessionStorage.getItem("sv_access_token")).toBeNull();
  });
});
