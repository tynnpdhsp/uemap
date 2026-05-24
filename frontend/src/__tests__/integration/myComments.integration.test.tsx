import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import { activeProfile } from "./helpers/fixtures";

const myCommentsList = {
  data: [
    {
      id: "cmt-001",
      content_preview: "Quán ăn này rất ngon, giá cả hợp lý cho sinh viên...",
      place_name: "Quán Cơm Sinh Viên",
      place_public_id: 1,
      status_label: "Hiển thị",
      created_at_display: "24/05/2026 10:00",
    },
    {
      id: "cmt-002",
      content_preview: "Phòng tự học tầng 3 rộng rãi, yên tĩnh...",
      place_name: "Thư viện Trường",
      place_public_id: 2,
      status_label: "Hiển thị",
      created_at_display: "23/05/2026 14:30",
    },
    {
      id: "cmt-003",
      content_preview: "ATM ở đây hay bị lỗi, nên cẩn thận...",
      place_name: "ATM VCB",
      place_public_id: 3,
      status_label: "Hiển thị",
      created_at_display: "22/05/2026 09:15",
    },
  ],
  meta: { page: 1, page_size: 20, total: 3 },
};

const emptyCommentsList = {
  data: [],
  meta: { page: 1, page_size: 20, total: 0 },
};

describe("integration: quản lý bình luận của tôi", () => {
  beforeEach(() => {
    sessionStorage.setItem("sv_access_token", "my-comments-token");
  });

  it("hiển thị danh sách bình luận với thông tin địa điểm", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/comments")) {
        return jsonOk(myCommentsList);
      }
      return null;
    });

    renderApp(["/my/comments"]);

    expect(await screen.findByText(/Quán ăn này rất ngon/)).toBeInTheDocument();
    expect(screen.getByText("Bình luận của tôi")).toBeInTheDocument();
    expect(screen.getByText(/Phòng tự học tầng 3 rộng rãi/)).toBeInTheDocument();
    expect(screen.getByText(/ATM ở đây hay bị lỗi/)).toBeInTheDocument();
    expect(screen.getByText("Quán Cơm Sinh Viên")).toBeInTheDocument();
    expect(screen.getByText("Thư viện Trường")).toBeInTheDocument();
    expect(screen.getByText("ATM VCB")).toBeInTheDocument();
  });

  it("hiển thị trạng thái trống khi chưa có bình luận", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/comments")) {
        return jsonOk(emptyCommentsList);
      }
      return null;
    });

    renderApp(["/my/comments"]);

    expect(await screen.findByText("Chưa có bình luận nào")).toBeInTheDocument();
    expect(screen.getByText("Bạn chưa gửi bình luận nào trên hệ thống.")).toBeInTheDocument();
  });

  it("xóa bình luận sau xác nhận cập nhật danh sách", async () => {
    const user = userEvent.setup();
    let deleted = false;

    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);

    const updatedList = {
      data: [
        myCommentsList.data[0],
        myCommentsList.data[2],
      ],
      meta: { page: 1, page_size: 20, total: 2 },
    };

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/comments")) {
        return jsonOk(deleted ? updatedList : myCommentsList);
      }
      if (method === "DELETE" && url.includes("/api/comments/cmt-002")) {
        deleted = true;
        return jsonOk(null);
      }
      return null;
    });

    renderApp(["/my/comments"]);

    expect(await screen.findByText(/Phòng tự học tầng 3 rộng rãi/)).toBeInTheDocument();

    const deleteButtons = screen.getAllByTitle("Xóa bình luận");
    await user.click(deleteButtons[1]);

    await waitFor(() => {
      expect(screen.queryByText(/Phòng tự học tầng 3 rộng rãi/)).not.toBeInTheDocument();
    });

    confirmSpy.mockRestore();
  });

  it("hủy xóa bình luận khi không xác nhận", async () => {
    const user = userEvent.setup();

    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(false);

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/comments")) {
        return jsonOk(myCommentsList);
      }
      return null;
    });

    renderApp(["/my/comments"]);

    expect(await screen.findByText(/Quán ăn này rất ngon/)).toBeInTheDocument();

    const deleteButtons = screen.getAllByTitle("Xóa bình luận");
    await user.click(deleteButtons[0]);

    expect(screen.getByText(/Quán ăn này rất ngon/)).toBeInTheDocument();

    confirmSpy.mockRestore();
  });

  it("chưa đăng nhập truy cập /my/comments chuyển hướng về /login", async () => {
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

    renderApp(["/my/comments"]);

    expect(await screen.findByRole("heading", { name: "Đăng Nhập" })).toBeInTheDocument();
  });

  it("hiển thị ngày tạo và trạng thái bình luận", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/comments")) {
        return jsonOk(myCommentsList);
      }
      return null;
    });

    renderApp(["/my/comments"]);

    expect(await screen.findByText("24/05/2026 10:00")).toBeInTheDocument();
    expect(screen.getByText("23/05/2026 14:30")).toBeInTheDocument();

    const statusLabels = screen.getAllByText("Hiển thị");
    expect(statusLabels.length).toBe(3);
  });
});
