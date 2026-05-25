export const TEST_EMAIL = "4901104172@student.hcmue.edu.vn";
export const TEST_PASSWORD = "testpassword123";
export const TEST_NEW_PASSWORD = "newsecurepassword123";
export const TEST_NAME = "Nguyễn Văn A";
export const TEST_OTP = "111111";
export const TEST_RESET_TOKEN = "reset-token-integration";

export const activeProfile = {
  id: "student-test-id",
  email: TEST_EMAIL,
  full_name: TEST_NAME,
  status: "active",
  status_label: "Đã kích hoạt",
  activated_at_display: "01/01/2025 10:00",
  locked_reason: null,
};

export const registerSuccessBody = {
  email: TEST_EMAIL,
  status: "pending_activation",
  otp_resend_available_at: "2025-01-01T00:00:00.000Z",
};

export const defaultPlaceListItems = [
  {
    public_id: 1,
    name: "Quán Phở 24h",
    category_name: "Ăn uống",
    address_short: "12 Nguyễn Tri Phương",
    updated_at_display: "25/05/2026 10:00",
  },
  {
    public_id: 2,
    name: "Thư viện Trường",
    category_name: "Học tập",
    address_short: "280 An Dương Vương",
    updated_at_display: "24/05/2026 15:30",
  },
  {
    public_id: 3,
    name: "ATM VCB",
    category_name: "Tiện ích",
    address_short: "300 An Dương Vương",
    updated_at_display: "23/05/2026 09:00",
  },
];

export function isPlacesListRequest(url: string, method: string): boolean {
  return (
    method === "GET" &&
    /\/api\/places(\?|$)/.test(url) &&
    !url.includes("/markers")
  );
}

export function jsonPlacesList(
  items = defaultPlaceListItems,
  meta?: { page: number; page_size: number; total: number },
) {
  return {
    status: 200,
    body: {
      success: true,
      data: items,
      meta: meta ?? { page: 1, page_size: 20, total: items.length },
    },
  };
}
