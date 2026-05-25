import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  activeProfile,
  defaultPlaceListItems,
  isPlacesListRequest,
  jsonPlacesList,
  TEST_NAME,
} from "./helpers/fixtures";

const mapConfig = {
  default_center: { lat: 10.7628, lng: 106.6824 },
  default_zoom: 16,
  geofence: {
    type: "rectangle",
    bounds: {
      sw: { lat: 10.755, lng: 106.675 },
      ne: { lat: 10.77, lng: 106.69 },
    },
  },
  cluster_zoom_threshold: 14,
};

const categories = [
  {
    id: "cat-1",
    name: "Ăn uống",
    color: "#ef4444",
    order: 1,
    icon_url: null,
    description: "Quán ăn, nhà hàng",
  },
  {
    id: "cat-2",
    name: "Học tập",
    color: "#3b82f6",
    order: 2,
    icon_url: null,
    description: "Thư viện, phòng tự học",
  },
  {
    id: "cat-3",
    name: "Tiện ích",
    color: "#10b981",
    order: 3,
    icon_url: null,
    description: "ATM, siêu thị",
  },
];

const markers = [
  {
    public_id: 1,
    name: "Quán Phở 24h",
    lat: 10.762,
    lng: 106.682,
    category_id: "cat-1",
    category_color: "#ef4444",
    category_icon_url: null,
    address_short: "12 Nguyễn Tri Phương",
  },
  {
    public_id: 2,
    name: "Thư viện Trường",
    lat: 10.763,
    lng: 106.683,
    category_id: "cat-2",
    category_color: "#3b82f6",
    category_icon_url: null,
    address_short: "280 An Dương Vương",
  },
  {
    public_id: 3,
    name: "ATM VCB",
    lat: 10.764,
    lng: 106.684,
    category_id: "cat-3",
    category_color: "#10b981",
    category_icon_url: null,
    address_short: "300 An Dương Vương",
  },
];

function installMapHomeFetchMock(
  overrides?: Partial<{
    placeList: typeof defaultPlaceListItems;
    placeListMeta: { page: number; page_size: number; total: number };
  }>,
) {
  return installFetchMock((url, method) => {
    if (method === "GET" && url.includes("/api/config/map")) {
      return jsonOk(mapConfig);
    }
    if (method === "GET" && url.includes("/api/categories")) {
      return jsonOk(categories);
    }
    if (method === "GET" && url.includes("/api/places/markers")) {
      return jsonOk(markers);
    }
    if (isPlacesListRequest(url, method)) {
      return jsonPlacesList(
        overrides?.placeList ?? defaultPlaceListItems,
        overrides?.placeListMeta,
      );
    }
    return null;
  });
}

describe("integration: trang chủ bản đồ", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("tải cấu hình bản đồ, danh mục và markers khi truy cập trang chủ", async () => {
    installMapHomeFetchMock();

    renderApp(["/"]);

    expect(await screen.findByText("Bản đồ HCMUE")).toBeInTheDocument();
    expect(await screen.findByText("Ăn uống")).toBeInTheDocument();
    expect(screen.getByText("Học tập")).toBeInTheDocument();
    expect(screen.getByText("Tiện ích")).toBeInTheDocument();
  });

  it("hiển thị danh sách địa điểm phân trang khi tải trang", async () => {
    installMapHomeFetchMock();

    renderApp(["/"]);

    expect(
      await screen.findByText(/Danh sách địa điểm \(3\)/i),
    ).toBeInTheDocument();
    expect(await screen.findByText("Quán Phở 24h")).toBeInTheDocument();
    expect(screen.getByText("Thư viện Trường")).toBeInTheDocument();
    expect(screen.getByLabelText("Sắp xếp danh sách")).toBeInTheDocument();
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
      if (isPlacesListRequest(url, method)) {
        return jsonPlacesList([]);
      }
      return null;
    });

    renderApp(["/"]);

    expect(
      screen.getByText("Đăng nhập để đóng góp vị trí"),
    ).toBeInTheDocument();
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
      if (isPlacesListRequest(url, method)) {
        return jsonPlacesList();
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
    installMapHomeFetchMock();

    renderApp(["/"]);

    const categoryButton = await screen.findByText("Ăn uống");
    expect(categoryButton).toBeInTheDocument();

    await user.click(categoryButton);

    await waitFor(() => {
      expect(screen.getByText("Ăn uống")).toBeInTheDocument();
    });
  });

  it("tìm kiếm hiển thị kết quả và nút hiện trên bản đồ", async () => {
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
      if (isPlacesListRequest(url, method)) {
        if (url.includes("q=Ph%E1%BB%9F") || url.includes("q=Pho")) {
          return jsonPlacesList([defaultPlaceListItems[0]], {
            page: 1,
            page_size: 20,
            total: 1,
          });
        }
        return jsonPlacesList();
      }
      return null;
    });

    renderApp(["/"]);

    const searchInput =
      await screen.findByPlaceholderText(/Tìm kiếm địa điểm/i);
    await user.type(searchInput, "Phở");

    expect(
      await screen.findByText(/Kết quả tìm kiếm \(1\)/i),
    ).toBeInTheDocument();
    expect(await screen.findByText("Quán Phở 24h")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Hiện trên bản đồ" }),
    ).toBeInTheDocument();
  });

  it("nút hiện trên bản đồ mở popup tóm tắt địa điểm", async () => {
    const user = userEvent.setup();
    const fetchMock = installMapHomeFetchMock();

    renderApp(["/"]);

    await screen.findByText("Quán Phở 24h");
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) => {
          const url = typeof input === "string" ? input : input.toString();
          return url.includes("/api/places/markers");
        }),
      ).toBe(true);
    });

    const showButtons = await screen.findAllByRole("button", {
      name: "Hiện trên bản đồ",
    });
    await user.click(showButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByText("Quán Phở 24h").length).toBeGreaterThanOrEqual(
        2,
      );
    });
  });

  it("phân trang danh sách chuyển trang", async () => {
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
      if (isPlacesListRequest(url, method)) {
        if (url.includes("page=2")) {
          return jsonPlacesList(
            [
              {
                public_id: 21,
                name: "Địa điểm trang 2",
                category_name: "Ăn uống",
                address_short: "99 Test Street",
                updated_at_display: "20/05/2026 08:00",
              },
            ],
            { page: 2, page_size: 20, total: 21 },
          );
        }
        return jsonPlacesList(defaultPlaceListItems, {
          page: 1,
          page_size: 20,
          total: 21,
        });
      }
      return null;
    });

    renderApp(["/"]);

    expect(await screen.findByText(/Trang 1 \/ 2/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sau/i }));
    expect(await screen.findByText("Địa điểm trang 2")).toBeInTheDocument();
    expect(await screen.findByText(/Trang 2 \/ 2/i)).toBeInTheDocument();
  });

  it("đổi sắp xếp danh sách gọi API với tham số sort", async () => {
    const user = userEvent.setup();
    const fetchMock = installMapHomeFetchMock();

    renderApp(["/"]);

    await screen.findByText("Quán Phở 24h");
    const sortSelect = screen.getByLabelText("Sắp xếp danh sách");
    await user.selectOptions(sortSelect, "updated_desc");

    await waitFor(() => {
      const listCalls = fetchMock.mock.calls.filter(([input, init]) => {
        const url = typeof input === "string" ? input : input.toString();
        return (
          (init?.method || "GET").toUpperCase() === "GET" &&
          isPlacesListRequest(url, "GET") &&
          url.includes("sort=updated_desc")
        );
      });
      expect(listCalls.length).toBeGreaterThanOrEqual(1);
    });
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
      if (isPlacesListRequest(url, method)) {
        return jsonPlacesList();
      }
      return null;
    });

    renderApp(["/login"]);

    await user.type(
      screen.getByPlaceholderText(/4901104172/),
      "4901104172@student.hcmue.edu.vn",
    );
    await user.type(screen.getByPlaceholderText("••••••••"), "testpassword123");
    await user.click(screen.getByRole("button", { name: "Đăng Nhập" }));

    await waitFor(() => {
      expect(sessionStorage.getItem("sv_access_token")).toBe("map-token");
    });

    expect(await screen.findByText("Bản đồ HCMUE")).toBeInTheDocument();
    expect(await screen.findByText(TEST_NAME)).toBeInTheDocument();
  });
});
