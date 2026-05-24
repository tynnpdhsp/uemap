import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import { activeProfile } from "./helpers/fixtures";

const myPlacesList = {
  data: [
    { public_id: 1, name: "Quán Cơm Sinh Viên", status: "published" as const, status_label: "Đã đăng", public_url: "/places/1" },
    { public_id: 2, name: "Phòng tự học tầng 3", status: "draft" as const, status_label: "Bản nháp", public_url: null },
    { public_id: 3, name: "Xe ôm công nghệ", status: "hidden" as const, status_label: "Bị ẩn", public_url: null },
  ],
  meta: { page: 1, page_size: 20, total: 3 },
};

const emptyPlacesList = {
  data: [],
  meta: { page: 1, page_size: 20, total: 0 },
};

describe("integration: quản lý địa điểm của tôi", () => {
  beforeEach(() => {
    sessionStorage.setItem("sv_access_token", "my-places-token");
  });

  it("hiển thị danh sách địa điểm với đầy đủ thông tin", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        return jsonOk(myPlacesList);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText("Quán Cơm Sinh Viên")).toBeInTheDocument();
    expect(screen.getByText("Địa điểm của tôi")).toBeInTheDocument();
    expect(screen.getByText("Phòng tự học tầng 3")).toBeInTheDocument();
    expect(screen.getByText("Xe ôm công nghệ")).toBeInTheDocument();
    expect(screen.getByText("Đã đăng", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText("Bản nháp", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText("Bị ẩn", { selector: "span" })).toBeInTheDocument();
  });

  it("hiển thị trạng thái trống khi chưa có địa điểm nào", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        return jsonOk(emptyPlacesList);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText("Chưa có địa điểm nào")).toBeInTheDocument();
    expect(screen.getByText("Đăng ký Địa điểm đầu tiên")).toBeInTheDocument();
  });

  it("bộ lọc trạng thái hoạt động và cập nhật danh sách", async () => {
    const user = userEvent.setup();
    const draftOnlyList = {
      data: [
        { public_id: 2, name: "Phòng tự học tầng 3", status: "draft" as const, status_label: "Bản nháp", public_url: null },
      ],
      meta: { page: 1, page_size: 20, total: 1 },
    };

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        if (url.includes("status=draft")) {
          return jsonOk(draftOnlyList);
        }
        return jsonOk(myPlacesList);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText("Quán Cơm Sinh Viên")).toBeInTheDocument();

    const selectFilter = screen.getByRole("combobox");
    await user.selectOptions(selectFilter, "draft");

    await waitFor(() => {
      expect(screen.getByText("Phòng tự học tầng 3")).toBeInTheDocument();
    });
  });

  it("xóa địa điểm sau xác nhận hiển thị lại danh sách cập nhật", async () => {
    const user = userEvent.setup();
    let deleted = false;

    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);

    const updatedList = {
      data: [
        { public_id: 1, name: "Quán Cơm Sinh Viên", status: "published" as const, status_label: "Đã đăng", public_url: "/places/1" },
        { public_id: 3, name: "Xe ôm công nghệ", status: "hidden" as const, status_label: "Bị ẩn", public_url: null },
      ],
      meta: { page: 1, page_size: 20, total: 2 },
    };

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        return jsonOk(deleted ? updatedList : myPlacesList);
      }
      if (method === "DELETE" && url.includes("/api/my/places/2")) {
        deleted = true;
        return jsonOk(null);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText("Phòng tự học tầng 3")).toBeInTheDocument();

    const deleteButtons = screen.getAllByTitle("Xóa");
    await user.click(deleteButtons[1]);

    await waitFor(() => {
      expect(screen.queryByText("Phòng tự học tầng 3")).not.toBeInTheDocument();
    });

    confirmSpy.mockRestore();
  });

  it("chưa đăng nhập truy cập /my/places chuyển hướng về /login", async () => {
    sessionStorage.clear();

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/config/map")) {
        return jsonOk({ default_center: { lat: 10.7628, lng: 106.6824 }, default_zoom: 16, geofence: null });
      }
      if (method === "GET" && url.includes("/api/categories")) {
        return jsonOk([]);
      }
      if (method === "GET" && url.includes("/api/places/markers")) {
        return jsonOk([]);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByRole("heading", { name: "Đăng Nhập" })).toBeInTheDocument();
  });

  it("hiển thị nút đóng góp địa điểm mới", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        return jsonOk(myPlacesList);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText("Quán Cơm Sinh Viên")).toBeInTheDocument();
    expect(screen.getByText("Đóng góp địa điểm mới")).toBeInTheDocument();
  });

  it("hiển thị tổng số địa điểm", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/places")) {
        return jsonOk(myPlacesList);
      }
      return null;
    });

    renderApp(["/my/places"]);

    expect(await screen.findByText(/Tổng số: 3/)).toBeInTheDocument();
  });
});
