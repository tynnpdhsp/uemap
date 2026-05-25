import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PlaceFormPage from "../../pages/student/PlaceFormPage";
import { mapApi } from "../../api/map";
import { placesApi } from "../../api/places";
import { renderWithRouter } from "../testUtils";

jest.mock("../../api/map", () => ({
  mapApi: {
    getConfig: jest.fn(),
    getCategories: jest.fn(),
  },
}));

jest.mock("../../api/places", () => ({
  placesApi: {
    create: jest.fn(),
    update: jest.fn(),
    getMyPlaceDetail: jest.fn(),
  },
}));

jest.mock("../../api/uploads", () => ({
  uploadsApi: {
    uploadImages: jest.fn(),
    uploadVideo: jest.fn(),
  },
}));

const mockGetConfig = mapApi.getConfig as jest.Mock;
const mockGetCategories = mapApi.getCategories as jest.Mock;
const mockCreate = placesApi.create as jest.Mock;

const defaultMapConfig = {
  default_center: { lat: 10.7628, lng: 106.6824 },
  default_zoom: 16,
  geofence: null,
};

describe("PlaceFormPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetConfig.mockResolvedValue({
      success: true,
      data: defaultMapConfig,
    });
    mockGetCategories.mockResolvedValue({
      success: true,
      data: [{ id: "cat-1", name: "Quán ăn", color: "#ff0000" }],
    });
  });

  it("hiển thị ô nhập vĩ độ/kinh độ với giá trị mặc định từ cấu hình bản đồ", async () => {
    renderWithRouter(<PlaceFormPage />, { route: "/my/places/new" });

    const latInput = await screen.findByLabelText("Vĩ độ (lat)");
    const lngInput = screen.getByLabelText("Kinh độ (lng)");

    expect(latInput).toHaveValue("10.762800");
    expect(lngInput).toHaveValue("106.682400");
    expect(screen.getByText("Tọa độ địa điểm *")).toBeInTheDocument();
  });

  it("cập nhật tọa độ khi nhập vĩ độ/kinh độ hợp lệ", async () => {
    const user = userEvent.setup();
    renderWithRouter(<PlaceFormPage />, { route: "/my/places/new" });

    const latInput = await screen.findByLabelText("Vĩ độ (lat)");
    const lngInput = screen.getByLabelText("Kinh độ (lng)");

    await user.clear(latInput);
    await user.type(latInput, "10.800000");
    await user.clear(lngInput);
    await user.type(lngInput, "106.700000");

    expect(latInput).toHaveValue("10.800000");
    expect(lngInput).toHaveValue("106.700000");
    expect(screen.queryByText(/Vĩ độ phải là số/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Kinh độ phải là số/)).not.toBeInTheDocument();
  });

  it("hiển thị lỗi khi vĩ độ không hợp lệ", async () => {
    const user = userEvent.setup();
    renderWithRouter(<PlaceFormPage />, { route: "/my/places/new" });

    const latInput = await screen.findByLabelText("Vĩ độ (lat)");
    await user.clear(latInput);
    await user.type(latInput, "95");

    expect(
      screen.getByText("Vĩ độ phải là số từ -90 đến 90."),
    ).toBeInTheDocument();
  });

  it("chặn đăng công khai khi tọa độ không hợp lệ", async () => {
    const user = userEvent.setup();
    renderWithRouter(<PlaceFormPage />, { route: "/my/places/new" });

    await screen.findByLabelText("Vĩ độ (lat)");

    await user.type(
      screen.getByPlaceholderText("Ví dụ: Quán cơm tấm HCMUE ngon..."),
      "Quán test tọa độ",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Giới thiệu về địa điểm, giá cả, đánh giá cá nhân (tối thiểu 20 ký tự khi đăng)...",
      ),
      "Mô tả đủ dài để đăng công khai địa điểm này.",
    );
    await user.type(
      screen.getByPlaceholderText("Số 280 An Dương Vương, Phường 4, Quận 5..."),
      "123 Đường Test, Q5",
    );

    const latInput = screen.getByLabelText("Vĩ độ (lat)");
    await user.clear(latInput);
    await user.type(latInput, "abc");

    await user.click(screen.getByRole("button", { name: /Đăng công khai/i }));

    expect(
      await screen.findByText(
        "Vui lòng chọn tọa độ trên bản đồ hoặc nhập vĩ độ/kinh độ hợp lệ.",
      ),
    ).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("gửi tọa độ đã nhập khi đăng công khai", async () => {
    const user = userEvent.setup();
    mockCreate.mockResolvedValue({ success: true, data: { public_id: 99 } });

    renderWithRouter(<PlaceFormPage />, { route: "/my/places/new" });

    await screen.findByLabelText("Vĩ độ (lat)");

    await user.type(
      screen.getByPlaceholderText("Ví dụ: Quán cơm tấm HCMUE ngon..."),
      "Quán test submit",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Giới thiệu về địa điểm, giá cả, đánh giá cá nhân (tối thiểu 20 ký tự khi đăng)...",
      ),
      "Mô tả đủ dài để đăng công khai địa điểm này.",
    );
    await user.type(
      screen.getByPlaceholderText("Số 280 An Dương Vương, Phường 4, Quận 5..."),
      "123 Đường Test, Q5",
    );

    const latInput = screen.getByLabelText("Vĩ độ (lat)");
    const lngInput = screen.getByLabelText("Kinh độ (lng)");
    await user.clear(latInput);
    await user.type(latInput, "10.800000");
    await user.clear(lngInput);
    await user.type(lngInput, "106.700000");

    await user.click(screen.getByRole("button", { name: /Đăng công khai/i }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          lat: 10.8,
          lng: 106.7,
          status: "published",
        }),
      );
    });
  });
});
