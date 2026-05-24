import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { getErrorMessage } from "../../utils/errorMessage";

export const ForgotVerifyOtpPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = searchParams.get("email") || "";

  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (!email) {
      setErrorMsg("Không tìm thấy thông tin email sinh viên.");
    }
  }, [email]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp || otp.length !== 6) {
      setErrorMsg("Mã OTP phải gồm đúng 6 chữ số");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await api.post<{ reset_token: string }>("/auth/forgot-password/verify", {
        email,
        otp,
      });

      if (res.success && res.data?.reset_token) {
        setSuccessMsg(
          "Xác thực mã OTP thành công! Chuyển đến trang đặt lại mật khẩu.",
        );
        const token = res.data.reset_token;
        setTimeout(() => {
          navigate(
            `/forgot-password/reset?email=${encodeURIComponent(email)}&token=${encodeURIComponent(token)}`,
          );
        }, 1500);
      } else {
        setErrorMsg("Không nhận được token đặt lại mật khẩu.");
      }
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Xác thực OTP thất bại."));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0) return;

    setResending(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await api.post("/auth/otp/resend", {
        email,
        purpose: "password_reset",
      });

      if (res.success) {
        setSuccessMsg("Mã OTP khôi phục mới đã được gửi tới email của bạn.");
        setCooldown(60);
      }
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Không thể gửi lại mã OTP."));
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-blue-100 via-white to-blue-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-gray-100">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Xác Thực OTP Quên Mật Khẩu
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Hệ thống đã gửi một mã OTP 6 số đến email khôi phục <br />
            <strong className="text-gray-800 break-all">{email}</strong>
          </p>
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

        <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label className="block text-center text-sm font-semibold text-gray-700 mb-2">
              Nhập Mã OTP 6 Số
            </label>
            <input
              type="text"
              required
              maxLength={6}
              className="w-full tracking-[1.5em] text-center rounded-lg border border-gray-300 px-4 py-3 text-2xl font-bold focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !email}
            className="w-full rounded-lg bg-blue-600 py-3 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300"
          >
            {loading ? "Đang xác thực..." : "Xác Thực Mã OTP"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={handleResend}
            disabled={cooldown > 0 || resending || !email}
            className="font-semibold text-blue-600 hover:text-blue-800 transition disabled:text-gray-400"
          >
            {resending
              ? "Đang gửi lại..."
              : cooldown > 0
                ? `Gửi lại mã sau ${cooldown} giây`
                : "Gửi lại mã OTP"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ForgotVerifyOtpPage;
