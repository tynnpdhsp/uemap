import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PlaceDetailPage from "../../pages/public/PlaceDetailPage";
import { placesApi } from "../../api/places";
import { commentsApi } from "../../api/comments";
import { reportsApi } from "../../api/reports";
import { useAuth } from "../../context/AuthContext";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/places", () => ({
  placesApi: {
    getDetail: jest.fn(),
  },
}));

jest.mock("../../api/comments", () => ({
  commentsApi: {
    getPlaceComments: jest.fn(),
    createComment: jest.fn(),
  },
}));

jest.mock("../../api/reports", () => ({
  reportsApi: {
    create: jest.fn(),
  },
}));

jest.mock("../../context/AuthContext", () => ({
  useAuth: jest.fn(),
}));

const mockGetDetail = placesApi.getDetail as jest.Mock;
const mockGetPlaceComments = commentsApi.getPlaceComments as jest.Mock;
const mockCreateComment = commentsApi.createComment as jest.Mock;
const mockCreateReport = reportsApi.create as jest.Mock;
const mockUseAuth = useAuth as jest.Mock;

const mockPlace = {
  public_id: 123,
  creator_student_id: "student-1",
  creator_student_name: "Nguyễn Văn A",
  category_id: "cat-1",
  category_name: "Quán ăn",
  scope_type: "near_campus",
  scope_label: "Gần trường",
  name: "Cơm tấm Cali",
  description: "Cơm tấm sườn bì chả ngon rẻ.",
  address: "123 An Dương Vương, Q5",
  location: {
    type: "Point",
    coordinates: [106.6824, 10.7628],
  },
  hours: "07:00 - 22:00",
  contact: "0901234567",
  images: [{ object_key: "img-1", sort_order: 0, mime: "image/jpeg" }],
  video: null,
  updated_at_display: "01/01/2026",
};

const mockComments = {
  data: [
    {
      id: "comm-1",
      author_display_name: "Lê Văn B",
      content: "Chất lượng tốt, phục vụ nhanh chóng.",
      created_at_display: "10 phút trước",
    },
  ],
  meta: {
    page: 1,
    page_size: 20,
    total: 1,
  },
};

describe("PlaceDetailPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetDetail.mockResolvedValue({ success: true, data: mockPlace });
    mockGetPlaceComments.mockResolvedValue({
      success: true,
      data: mockComments,
    });
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      student: { full_name: "Nguyễn Văn A", status: "active" },
    });
  });

  it("hiển thị chi tiết địa điểm và danh sách bình luận", async () => {
    renderWithRouter(<PlaceDetailPage />, {
      route: "/places/123",
      routes: [{ path: "/places/:publicId", element: <PlaceDetailPage /> }],
    });

    expect(await screen.findByText("Cơm tấm Cali")).toBeInTheDocument();
    expect(screen.getByText("Quán ăn")).toBeInTheDocument();
    expect(screen.getByText("Gần trường")).toBeInTheDocument();
    expect(screen.getByText("123 An Dương Vương, Q5")).toBeInTheDocument();
    expect(screen.getByText("07:00 - 22:00")).toBeInTheDocument();
    expect(screen.getByText("0901234567")).toBeInTheDocument();
    expect(screen.getByText("Lê Văn B")).toBeInTheDocument();
    expect(
      screen.getByText("Chất lượng tốt, phục vụ nhanh chóng."),
    ).toBeInTheDocument();
  });

  it("cho phép gửi bình luận mới khi sinh viên là active", async () => {
    const user = userEvent.setup();
    mockCreateComment.mockResolvedValue({
      success: true,
      data: {
        id: "comm-2",
        author_display_name: "Nguyễn Văn A",
        content: "Phù hợp với túi tiền sinh viên.",
        created_at_display: "Vừa xong",
      },
    });

    renderWithRouter(<PlaceDetailPage />, {
      route: "/places/123",
      routes: [{ path: "/places/:publicId", element: <PlaceDetailPage /> }],
    });

    await screen.findByText("Cơm tấm Cali");

    const textarea = screen.getByPlaceholderText(/Chia sẻ nhận xét của bạn/i);
    await user.type(textarea, "Phù hợp với túi tiền sinh viên.");

    const submitBtn = screen.getByRole("button", { name: "" });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockCreateComment).toHaveBeenCalledWith(
        123,
        "Phù hợp với túi tiền sinh viên.",
      );
    });
  });

  it("gửi báo cáo vi phạm thành công", async () => {
    const user = userEvent.setup();
    mockCreateReport.mockResolvedValue({
      success: true,
      data: {
        report_code: "RP-20260525-0001",
        status: "new",
        status_label: "Mới nhận",
        created_at_display: "Vừa xong",
      },
    });

    renderWithRouter(<PlaceDetailPage />, {
      route: "/places/123",
      routes: [{ path: "/places/:publicId", element: <PlaceDetailPage /> }],
    });

    await screen.findByText("Cơm tấm Cali");

    const reportBtn = screen.getByRole("button", { name: /Báo cáo Vi phạm/i });
    await user.click(reportBtn);

    expect(
      await screen.findByRole("heading", { name: "Báo cáo Vi phạm" }),
    ).toBeInTheDocument();

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "wrong_info");

    const reasonTextarea = screen.getByPlaceholderText(
      /Mô tả chi tiết vi phạm/i,
    );
    await user.type(reasonTextarea, "Địa điểm này đã đóng cửa từ rất lâu rồi.");

    const submitReportBtn = screen.getByRole("button", { name: "Gửi Báo cáo" });
    await user.click(submitReportBtn);

    expect(await screen.findByText(/RP-20260525-0001/)).toBeInTheDocument();
  });
});
