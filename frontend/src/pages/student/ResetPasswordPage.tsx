import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = searchParams.get("email") || "";
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!email || !token) {
      setErrorMsg("Yêu cầu đặt lại mật khẩu không hợp lệ hoặc thiếu thông tin xác thực.");
    }
  }, [email, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (password.length < 8 || password.length > 128) {
      setErrorMsg("Mật khẩu phải dài từ 8 đến 128 ký tự");
      return;
    }
    if (password !== passwordConfirm) {
      setErrorMsg("Mật khẩu xác nhận không khớp");
      return;
    }

    setLoading(true);

    try {
      const res = await api.post("/auth/forgot-password/reset", {
        email,
        reset_token: token,
        password
      });

      if (res.success) {
        setSuccessMsg("Đặt lại mật khẩu thành công! Bạn sẽ được chuyển tới trang đăng nhập.");
        setTimeout(() => {
          navigate("/login");
        }, 3000);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Đặt lại mật khẩu thất bại. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-blue-100 via-white to-blue-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-gray-100">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Đặt Lại Mật Khẩu</h2>
          <p className="mt-2 text-sm text-gray-500">Nhập mật khẩu mới cho tài khoản của bạn</p>
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
            {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
            {successMsg}
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-semibold text-gray-700">Mật Khẩu Mới</label>
            <input
              type="password"
              required
              disabled={!email || !token}
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition disabled:bg-gray-100"
              placeholder="Tối thiểu 8 ký tự"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700">Xác Nhận Mật Khẩu</label>
            <input
              type="password"
              required
              disabled={!email || !token}
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition disabled:bg-gray-100"
              placeholder="Nhập lại mật khẩu mới"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !email || !token}
            className="w-full rounded-lg bg-blue-600 py-3 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300"
          >
            {loading ? "Đang xử lý..." : "Đặt Lại Mật Khẩu"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
