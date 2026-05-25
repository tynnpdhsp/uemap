import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk, jsonError } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import {
  activeProfile,
  isPlacesListRequest,
  jsonPlacesList,
} from "./helpers/fixtures";

const mapConfig = {
  default_center: { lat: 10.7628, lng: 106.6824 },
  default_zoom: 16,
  geofence: null,
};

const placeDetail = {
  public_id: 1,
  creator_student_id: "stu-001",
  creator_student_name: "Nguyễn Văn B",
  category_id: "cat-1",
  category_name: "Ăn uống",
  scope_type: "internal",
  scope_label: "Nội bộ trường",
  name: "Quán Phở 24h Ngon Nhất",
  description: "Quán phở mở cửa 24/7 phục vụ sinh viên.",
  address: "12 Nguyễn Tri Phương, Quận 5, TP.HCM",
  location: { type: "Point", coordinates: [106.682, 10.762] },
  hours: "00:00 - 23:59",
  contact: "0901234567",
  images: [
    { object_key: "places/1/img1.jpg", sort_order: 0, mime: "image/jpeg" },
    { object_key: "places/1/img2.jpg", sort_order: 1, mime: "image/jpeg" },
  ],
  video: { kind: "embed", url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ" },
  updated_at_display: "25/05/2026 08:30",
};

const commentsPage1 = {
  data: [
    {
      id: "cmt-1",
      author_display_name: "Trần Văn C",
      content: "Quán phở ở đây rất ngon, giá cả phải chăng!",
      created_at_display: "24/05/2026 10:00",
    },
    {
      id: "cmt-2",
      author_display_name: "Lê Thị D",
      content: "Không gian sạch sẽ, phục vụ nhanh.",
      created_at_display: "23/05/2026 14:30",
    },
  ],
  meta: { page: 1, page_size: 20, total: 2 },
};

describe("integration: xem chi tiết địa điểm", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("hiển thị chi tiết địa điểm với đầy đủ thông tin", async () => {
    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
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

    renderApp(["/places/1"]);

    expect(
      await screen.findByText("Quán Phở 24h Ngon Nhất"),
    ).toBeInTheDocument();
    expect(screen.getByText("Ăn uống")).toBeInTheDocument();
    expect(screen.getByText("Nội bộ trường")).toBeInTheDocument();
    expect(
      screen.getByText("Quán phở mở cửa 24/7 phục vụ sinh viên."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("12 Nguyễn Tri Phương, Quận 5, TP.HCM"),
    ).toBeInTheDocument();
    expect(screen.getByText("00:00 - 23:59")).toBeInTheDocument();
    expect(screen.getByText("0901234567")).toBeInTheDocument();
    expect(screen.getByText("Vị trí trên bản đồ")).toBeInTheDocument();
  });

  it("mở lightbox ảnh khi nhấp vào album", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      return null;
    });

    renderApp(["/places/1"]);
    await screen.findByText("Quán Phở 24h Ngon Nhất");
    await user.click(screen.getByRole("button", { name: "Xem ảnh phóng to" }));

    expect(
      screen.getByRole("dialog", { name: "Xem ảnh phóng to" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
  });

  it("nhúng video Facebook Watch khi URL hợp lệ", async () => {
    const fbDetail = {
      ...placeDetail,
      video: {
        kind: "embed",
        url: "https://www.facebook.com/watch?v=987654321",
      },
    };

    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(fbDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      return null;
    });

    renderApp(["/places/1"]);
    await screen.findByText("Quán Phở 24h Ngon Nhất");

    const iframe = document.querySelector("iframe");
    expect(iframe?.getAttribute("src")).toContain(
      "facebook.com/plugins/video.php",
    );
  });

  it("hiển thị danh sách bình luận công khai", async () => {
    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      return null;
    });

    renderApp(["/places/1"]);

    expect(await screen.findByText("Trần Văn C")).toBeInTheDocument();
    expect(
      screen.getByText("Quán phở ở đây rất ngon, giá cả phải chăng!"),
    ).toBeInTheDocument();
    expect(screen.getByText("Lê Thị D")).toBeInTheDocument();
    expect(
      screen.getByText("Không gian sạch sẽ, phục vụ nhanh."),
    ).toBeInTheDocument();
  });

  it("chưa đăng nhập hiển thị lời mời đăng nhập thay vì form bình luận", async () => {
    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      return null;
    });

    renderApp(["/places/1"]);

    expect(await screen.findByText(/Đăng nhập/i)).toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText(/Chia sẻ nhận xét/i),
    ).not.toBeInTheDocument();
  });

  it("đã đăng nhập hiển thị form gửi bình luận và gửi thành công", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem("sv_access_token", "comment-token");

    let commentSubmitted = false;

    installFetchMock((url, method, body) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        if (commentSubmitted) {
          return jsonOk({
            data: [
              {
                id: "cmt-new",
                author_display_name: "Nguyễn Văn A",
                content: "Bình luận mới từ integration test",
                created_at_display: "25/05/2026 12:00",
              },
              ...commentsPage1.data,
            ],
            meta: { page: 1, page_size: 20, total: 3 },
          });
        }
        return jsonOk(commentsPage1);
      }
      if (method === "POST" && url.includes("/api/places/1/comments")) {
        commentSubmitted = true;
        return jsonOk({
          id: "cmt-new",
          author_display_name: "Nguyễn Văn A",
          content: (body as { content: string }).content,
          created_at_display: "25/05/2026 12:00",
        });
      }
      return null;
    });

    renderApp(["/places/1"]);

    const textarea = await screen.findByPlaceholderText(/Chia sẻ nhận xét/i);
    expect(textarea).toBeInTheDocument();

    await user.type(textarea, "Bình luận mới từ integration test");

    const submitButtons = screen.getAllByRole("button");
    const sendButton = submitButtons.find(
      (btn) =>
        btn.querySelector("svg") && btn.getAttribute("type") === "submit",
    );
    if (sendButton) {
      await user.click(sendButton);
    }

    expect(
      await screen.findByText("Bình luận mới từ integration test"),
    ).toBeInTheDocument();
  });

  it("đã đăng nhập hiển thị nút báo cáo vi phạm địa điểm", async () => {
    sessionStorage.setItem("sv_access_token", "report-token");

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      return null;
    });

    renderApp(["/places/1"]);

    expect(await screen.findByText("Báo cáo Vi phạm")).toBeInTheDocument();
  });

  it("gửi báo cáo vi phạm địa điểm thành công", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem("sv_access_token", "report-token");

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (
        method === "GET" &&
        url.includes("/api/places/1") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonOk(placeDetail);
      }
      if (method === "GET" && url.includes("/api/places/1/comments")) {
        return jsonOk(commentsPage1);
      }
      if (method === "POST" && url.includes("/api/reports")) {
        return jsonOk({
          report_code: "RP-20260525-0001",
          status: "new",
          status_label: "Mới gửi",
          created_at_display: "25/05/2026 12:00",
        });
      }
      return null;
    });

    renderApp(["/places/1"]);

    const reportButton = await screen.findByText("Báo cáo Vi phạm");
    await user.click(reportButton);

    expect(await screen.findByText(/Lý do chính/i)).toBeInTheDocument();

    const reasonTextarea = screen.getByPlaceholderText(
      /Mô tả chi tiết vi phạm/i,
    );
    await user.type(
      reasonTextarea,
      "Thông tin địa chỉ sai lệch, quán đã đóng cửa vĩnh viễn",
    );

    const submitButton = screen.getByRole("button", { name: /Gửi Báo cáo/i });
    await user.click(submitButton);

    expect(
      await screen.findByText("Gửi báo cáo thành công"),
    ).toBeInTheDocument();
    expect(screen.getByText("RP-20260525-0001")).toBeInTheDocument();
  });

  it("hiển thị lỗi khi địa điểm không tồn tại", async () => {
    installFetchMock((url, method) => {
      if (
        method === "GET" &&
        url.includes("/api/places/999") &&
        !url.includes("markers") &&
        !url.includes("comments")
      ) {
        return jsonError("Không tìm thấy địa điểm.", 404);
      }
      if (method === "GET" && url.includes("/api/places/999/comments")) {
        return jsonOk({ data: [], meta: { page: 1, page_size: 20, total: 0 } });
      }
      return null;
    });

    renderApp(["/places/999"]);

    expect(await screen.findByText("Đã xảy ra lỗi")).toBeInTheDocument();
    expect(screen.getByText("Quay lại Bản đồ")).toBeInTheDocument();
  });
});
