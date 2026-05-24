import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import { activeProfile, TEST_NAME } from "./helpers/fixtures";

const mapConfig = {
  default_center: { lat: 10.7628, lng: 106.6824 },
  default_zoom: 16,
  geofence: {
    type: "rectangle",
    bounds: {
      sw: { lat: 10.755, lng: 106.675 },
      ne: { lat: 10.770, lng: 106.690 },
    },
  },
  cluster_zoom_threshold: 14,
};

const categories = [
  { id: "cat-1", name: "Ăn uống", color: "#ef4444", order: 1, icon_url: null, description: "Quán ăn, nhà hàng" },
  { id: "cat-2", name: "Học tập", color: "#3b82f6", order: 2, icon_url: null, description: "Thư viện, phòng tự học" },
  { id: "cat-3", name: "Tiện ích", color: "#10b981", order: 3, icon_url: null, description: "ATM, siêu thị" },
];

const markers = [
  { public_id: 1, name: "Quán Phở 24h", lat: 10.762, lng: 106.682, category_id: "cat-1", category_color: "#ef4444", category_icon_url: null, address_short: "12 Nguyễn Tri Phương" },
  { public_id: 2, name: "Thư viện Trường", lat: 10.763, lng: 106.683, category_id: "cat-2", category_color: "#3b82f6", category_icon_url: null, address_short: "280 An Dương Vương" },
  { public_id: 3, name: "ATM VCB", lat: 10.764, lng: 106.684, category_id: "cat-3", category_color: "#10b981", category_icon_url: null, address_short: "300 An Dương Vương" },
];

describe("integration: trang chủ bản đồ", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("tải cấu hình bản đồ, danh mục và markers khi truy cập trang chủ", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk(categories);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk(markers);
      }
      return null;
    });

    renderApp(["/"]);

    expect(await screen.findByText("Bản đồ HCMUE")).toBeInTheDocument();
    expect(await screen.findByText("Ăn uống")).toBeInTheDocument();
    expect(screen.getByText("Học tập")).toBeInTheDocument();
    expect(screen.getByText("Tiện ích")).toBeInTheDocument();
  });

  it("hiển thị liên kết đăng nhập khi chưa xác thực", () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
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

    expect(screen.getByText("Đăng nhập để đóng góp vị trí")).toBeInTheDocument();
  });

  it("hiển thị nút đóng góp và tên sinh viên khi đã xác thực", async () => {
    sessionStorage.setItem("sv_access_token", "integration-token");

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk(categories);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk(markers);
      }
      return null;
    });

    renderApp(["/"]);

    expect(await screen.findByText(TEST_NAME)).toBeInTheDocument();
    expect(await screen.findByText(/Sinh viên:/i)).toBeInTheDocument();
    expect(screen.getByText("Đóng góp Địa điểm mới")).toBeInTheDocument();
  });

  it("bộ lọc danh mục hiển thị checkbox và có thể toggle", async () => {
    const user = userEvent.setup();

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk(categories);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk(markers);
      }
      return null;
    });

    renderApp(["/"]);

    const categoryButton = await screen.findByText("Ăn uống");
    expect(categoryButton).toBeInTheDocument();

    await user.click(categoryButton);

    await waitFor(() => {
      expect(screen.getByText("Ăn uống")).toBeInTheDocument();
    });
  });

  it("thanh tìm kiếm chấp nhận đầu vào", async () => {
    const user = userEvent.setup();

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk(categories);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk(markers);
      }
      return null;
    });

    renderApp(["/"]);

    const searchInput = await screen.findByPlaceholderText(/Tìm kiếm địa điểm/i);
    await user.type(searchInput, "Phở");

    expect(searchInput).toHaveValue("Phở");
  });

  it("đăng nhập rồi quay về trang chủ hiển thị đầy đủ bản đồ", async () => {
    const user = userEvent.setup();

    installFetchMock((url, method) => {
      if (method === "POST" && url.includes("/api/auth/login")) {
        return jsonOk({ access_token: "map-token" });
      }
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk(mapConfig);
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk(categories);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk(markers);
      }
      return null;
    });

    renderApp(["/login"]);

    await user.type(screen.getByPlaceholderText(/4901104172/), "4901104172@student.hcmue.edu.vn");
    await user.type(screen.getByPlaceholderText("••••••••"), "testpassword123");
    await user.click(screen.getByRole("button", { name: "Đăng Nhập" }));

    await waitFor(() => {
      expect(sessionStorage.getItem("sv_access_token")).toBe("map-token");
    });

    expect(await screen.findByText("Bản đồ HCMUE")).toBeInTheDocument();
    expect(await screen.findByText(TEST_NAME)).toBeInTheDocument();
  });
});
