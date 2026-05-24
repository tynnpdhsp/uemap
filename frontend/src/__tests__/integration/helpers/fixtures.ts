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
