import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isNotActivated, setIsNotActivated] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setIsNotActivated(false);

    try {
      const res = await login(email, password);
      if (res.success) {
        navigate("/");
      }
    } catch (err: any) {
      const msg = err.message || "Đăng nhập thất bại. Vui lòng thử lại.";
      setErrorMsg(msg);
      if (msg.includes("chưa được kích hoạt") || msg.includes("OTP")) {
        setIsNotActivated(true);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-blue-100 via-white to-blue-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-gray-100 transition-all hover:shadow-2xl">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Đăng Nhập</h2>
          <p className="mt-2 text-sm text-gray-500">Cổng thông tin Bản đồ Sinh viên Sư phạm</p>
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100 animate-pulse">
            {errorMsg}
            {isNotActivated && (
              <div className="mt-2 font-semibold">
                <Link
                  to={`/register/verify-otp?email=${encodeURIComponent(email)}`}
                  className="underline hover:text-red-900 text-blue-600"
                >
                  Nhấp vào đây để kích hoạt tài khoản bằng mã OTP
                </Link>
              </div>
            )}
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

          <div>
            <label className="block text-sm font-semibold text-gray-700">Mật Khẩu</label>
            <input
              type="password"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <Link to="/forgot-password" className="font-medium text-blue-600 hover:text-blue-800 transition">
              Quên mật khẩu?
            </Link>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300"
          >
            {loading ? "Đang xử lý..." : "Đăng Nhập"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Chưa có tài khoản?{" "}
          <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-800 transition">
            Đăng ký ngay
          </Link>
        </p>
      </div>
    </div>
  );
};
export default LoginPage;
