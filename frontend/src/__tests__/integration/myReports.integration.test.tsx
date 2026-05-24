import { screen } from "@testing-library/react";
import { installFetchMock, jsonOk } from "./helpers/fetchMock";
import { renderApp } from "./helpers/renderApp";
import { activeProfile } from "./helpers/fixtures";

const myReportsList = {
  data: [
    {
      report_code: "RP-20260524-0001",
      target_type: "place" as const,
      target_summary: "Quán Cơm Sinh Viên - thông tin sai",
      report_type_label: "Thông tin sai lệch",
      status_label: "Mới gửi",
      created_at_display: "24/05/2026 10:00",
    },
    {
      report_code: "RP-20260523-0002",
      target_type: "comment" as const,
      target_summary: "Bình luận spam quảng cáo trên quán phở",
      report_type_label: "Spam / Quảng cáo",
      status_label: "Đang xử lý",
      created_at_display: "23/05/2026 14:30",
    },
    {
      report_code: "RP-20260520-0003",
      target_type: "place" as const,
      target_summary: "Địa điểm không phù hợp nội quy",
      report_type_label: "Nội dung không phù hợp",
      status_label: "Đã xử lý",
      created_at_display: "20/05/2026 09:00",
    },
  ],
  meta: { page: 1, page_size: 20, total: 3 },
};

const emptyReportsList = {
  data: [],
  meta: { page: 1, page_size: 20, total: 0 },
};

describe("integration: báo cáo vi phạm của tôi", () => {
  beforeEach(() => {
    sessionStorage.setItem("sv_access_token", "my-reports-token");
  });

  it("hiển thị danh sách báo cáo với đầy đủ thông tin", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("RP-20260524-0001")).toBeInTheDocument();
    expect(screen.getByText("Báo cáo vi phạm của tôi")).toBeInTheDocument();
    expect(screen.getByText("RP-20260523-0002")).toBeInTheDocument();
    expect(screen.getByText("RP-20260520-0003")).toBeInTheDocument();
  });

  it("hiển thị mã báo cáo và loại vi phạm", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("Thông tin sai lệch")).toBeInTheDocument();
    expect(screen.getByText("Spam / Quảng cáo")).toBeInTheDocument();
    expect(screen.getByText("Nội dung không phù hợp")).toBeInTheDocument();
  });

  it("hiển thị tóm tắt đối tượng bị báo cáo", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(
      await screen.findByText("Quán Cơm Sinh Viên - thông tin sai"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Bình luận spam quảng cáo trên quán phở"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Địa điểm không phù hợp nội quy"),
    ).toBeInTheDocument();
  });

  it("hiển thị trạng thái xử lý khác nhau", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("Mới gửi")).toBeInTheDocument();
    expect(screen.getByText("Đang xử lý")).toBeInTheDocument();
    expect(screen.getByText("Đã xử lý")).toBeInTheDocument();
  });

  it("hiển thị loại đối tượng (địa điểm/bình luận)", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("RP-20260524-0001")).toBeInTheDocument();

    const placeLabels = screen.getAllByText(/địa điểm/i);
    expect(placeLabels.length).toBeGreaterThanOrEqual(2);

    const commentLabels = screen.getAllByText(/bình luận/i);
    expect(commentLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("hiển thị trạng thái trống khi chưa gửi báo cáo nào", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(emptyReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("Chưa gửi báo cáo nào")).toBeInTheDocument();
    expect(
      screen.getByText("Lịch sử gửi báo cáo của bạn trống."),
    ).toBeInTheDocument();
  });

  it("chưa đăng nhập truy cập /my/reports chuyển hướng về /login", async () => {
    sessionStorage.clear();

    installFetchMock((url, method) => {
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

    renderApp(["/my/reports"]);

    expect(
      await screen.findByRole("heading", { name: "Đăng Nhập" }),
    ).toBeInTheDocument();
  });

  it("hiển thị ngày tạo báo cáo", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/me")) {
        return jsonOk(activeProfile);
      }
      if (method === "GET" && url.includes("/api/my/reports")) {
        return jsonOk(myReportsList);
      }
      return null;
    });

    renderApp(["/my/reports"]);

    expect(await screen.findByText("24/05/2026 10:00")).toBeInTheDocument();
    expect(screen.getByText("23/05/2026 14:30")).toBeInTheDocument();
    expect(screen.getByText("20/05/2026 09:00")).toBeInTheDocument();
  });
});
