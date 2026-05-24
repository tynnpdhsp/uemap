import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const emailRegex = /^[0-9]{10}@student\.hcmue\.edu\.vn$/;
    if (!emailRegex.test(email.trim().toLowerCase())) {
      setErrorMsg("Email phải đúng định dạng mã số sinh viên 10 chữ số @student.hcmue.edu.vn");
      return;
    }

    setLoading(true);

    try {
      const res = await api.post("/auth/forgot-password", { email: email.trim() });
      if (res.success) {
        navigate(`/forgot-password/verify-otp?email=${encodeURIComponent(email.trim())}`);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Đã xảy ra lỗi. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-blue-100 via-white to-blue-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-gray-100">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Quên Mật Khẩu</h2>
          <p className="mt-2 text-sm text-gray-500">Nhập email của bạn để nhận mã OTP khôi phục mật khẩu</p>
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
            {errorMsg}
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-semibold text-gray-700">Email Sinh Viên</label>
            <input
              type="email"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="e.g. 4901104172@student.hcmue.edu.vn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300"
          >
            {loading ? "Đang xử lý..." : "Gửi Mã OTP"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm">
          <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-800 transition">
            Quay lại đăng nhập
          </Link>
        </div>
      </div>
    </div>
  );
};
export default ForgotPasswordPage;
