import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { getErrorMessage } from "../../utils/errorMessage";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [fullName, setFullName] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const emailRegex = /^[0-9]{10}@student\.hcmue\.edu\.vn$/;
    if (!emailRegex.test(email.trim().toLowerCase())) {
      setErrorMsg(
        "Email phải đúng định dạng mã số sinh viên 10 chữ số @student.hcmue.edu.vn",
      );
      return;
    }
    if (password.length < 8 || password.length > 128) {
      setErrorMsg("Mật khẩu phải dài từ 8 đến 128 ký tự");
      return;
    }
    if (password !== passwordConfirm) {
      setErrorMsg("Mật khẩu xác nhận không khớp");
      return;
    }
    if (fullName.trim().length < 5 || fullName.trim().length > 100) {
      setErrorMsg("Họ tên hiển thị phải từ 5 đến 100 ký tự");
      return;
    }
    if (!acceptTerms) {
      setErrorMsg("Bạn phải đồng ý với điều khoản dịch vụ");
      return;
    }

    setLoading(true);

    try {
      const res = await api.post("/auth/register", {
        email: email.trim(),
        password,
        password_confirm: passwordConfirm,
        full_name: fullName.trim(),
        accept_terms: acceptTerms,
      });

      if (res.success) {
        navigate(
          `/register/verify-otp?email=${encodeURIComponent(email.trim())}`,
        );
      }
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Đăng ký thất bại. Vui lòng thử lại."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-blue-100 via-white to-blue-50 px-4 py-8">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-gray-100 transition-all hover:shadow-2xl">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Đăng Ký
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Tạo tài khoản Bản đồ Sinh viên Sư phạm
          </p>
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
            {errorMsg}
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-semibold text-gray-700">
              Email Sinh Viên
            </label>
            <input
              type="email"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="4901104172@student.hcmue.edu.vn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700">
              Họ và Tên
            </label>
            <input
              type="text"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="e.g. Nguyễn Văn A"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700">
              Mật Khẩu
            </label>
            <input
              type="password"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="Tối thiểu 8 ký tự"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700">
              Xác Nhận Mật Khẩu
            </label>
            <input
              type="password"
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="Nhập lại mật khẩu"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="acceptTerms"
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
            />
            <label htmlFor="acceptTerms" className="ml-2 text-sm text-gray-600">
              Tôi đồng ý với{" "}
              <a
                href="#"
                className="font-semibold text-blue-600 hover:underline"
              >
                Điều khoản dịch vụ
              </a>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300"
          >
            {loading ? "Đang xử lý..." : "Đăng Ký"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Đã có tài khoản?{" "}
          <Link
            to="/login"
            className="font-semibold text-blue-600 hover:text-blue-800 transition"
          >
            Đăng nhập
          </Link>
        </p>
      </div>
    </div>
  );
};
export default RegisterPage;
