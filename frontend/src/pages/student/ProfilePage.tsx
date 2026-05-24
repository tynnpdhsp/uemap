import React, { useState, useEffect } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { getErrorMessage } from "../../utils/errorMessage";

interface StudentProfile {
  email: string;
  full_name: string;
  status: string;
  status_label: string;
  activated_at_display: string | null;
  locked_reason: string | null;
}

export const ProfilePage: React.FC = () => {
  const { logout } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(true);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [changePwdLoading, setChangePwdLoading] = useState(false);

  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwdError, setPwdError] = useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await api.get<StudentProfile>("/me");
      if (res.success && res.data) {
        setProfile(res.data);
        setFullName(res.data.full_name);
      }
    } catch {
      setProfileError("Không thể tải thông tin cá nhân. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);

    if (fullName.trim().length < 5 || fullName.trim().length > 100) {
      setProfileError("Họ tên hiển thị phải từ 5 đến 100 ký tự");
      return;
    }

    setUpdateLoading(true);
    try {
      const res = await api.patch<StudentProfile>("/me", { full_name: fullName.trim() });
      if (res.success && res.data) {
        setProfile(res.data);
        setProfileSuccess("Cập nhật thông tin cá nhân thành công.");
      }
    } catch (err: unknown) {
      setProfileError(getErrorMessage(err, "Cập nhật thất bại."));
    } finally {
      setUpdateLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);

    if (!currentPassword) {
      setPwdError("Vui lòng nhập mật khẩu hiện tại");
      return;
    }
    if (newPassword.length < 8 || newPassword.length > 128) {
      setPwdError("Mật khẩu mới phải dài từ 8 đến 128 ký tự");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdError("Mật khẩu xác nhận không khớp");
      return;
    }

    setChangePwdLoading(true);
    try {
      const res = await api.post("/me/change-password", {
        current_password: currentPassword,
        password: newPassword,
        password_confirm: confirmPassword,
      });

      if (res.success) {
        setPwdSuccess(
          "Đổi mật khẩu thành công! Các phiên đăng nhập khác của bạn đã bị đăng xuất.",
        );
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      }
    } catch (err: unknown) {
      setPwdError(getErrorMessage(err, "Đổi mật khẩu thất bại."));
    } finally {
      setChangePwdLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          Trang Cá Nhân
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          Quản lý thông tin tài khoản và mật khẩu của bạn
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-6">
          {/* Card thông tin tài khoản */}
          <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
            <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3">
              Tài Khoản
            </h2>
            <div className="mt-4 space-y-4 text-sm">
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase">
                  Email
                </span>
                <span className="text-gray-900 font-medium break-all">
                  {profile?.email}
                </span>
              </div>
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase">
                  Trạng Thái
                </span>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${
                    profile?.status === "active"
                      ? "bg-green-100 text-green-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  {profile?.status_label}
                </span>
              </div>
              {profile?.activated_at_display && (
                <div>
                  <span className="block text-xs font-semibold text-gray-400 uppercase">
                    Ngày kích hoạt
                  </span>
                  <span className="text-gray-900 font-medium">
                    {profile?.activated_at_display}
                  </span>
                </div>
              )}
            </div>
            <div className="mt-6 border-t border-gray-100 pt-4">
              <button
                onClick={() => logout()}
                className="w-full rounded-lg bg-red-50 py-2.5 text-red-600 font-bold hover:bg-red-100 transition text-sm"
              >
                Đăng Xuất
              </button>
            </div>
          </div>
        </div>

        <div className="md:col-span-2 space-y-8">
          {/* Card cập nhật thông tin */}
          <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
            <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3">
              Thông Tin Cá Nhân
            </h2>

            {profileError && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
                {profileError}
              </div>
            )}

            {profileSuccess && (
              <div className="mt-4 p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
                {profileSuccess}
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Họ và Tên Hiển Thị
                </label>
                <input
                  type="text"
                  required
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <button
                type="submit"
                disabled={updateLoading}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300 text-sm"
              >
                {updateLoading ? "Đang lưu..." : "Cập Nhật Thông Tin"}
              </button>
            </form>
          </div>

          {/* Card đổi mật khẩu */}
          <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
            <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3">
              Đổi Mật Khẩu
            </h2>

            {pwdError && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
                {pwdError}
              </div>
            )}

            {pwdSuccess && (
              <div className="mt-4 p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
                {pwdSuccess}
              </div>
            )}

            <form onSubmit={handleChangePassword} className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Mật Khẩu Hiện Tại
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Mật Khẩu Mới
                </label>
                <input
                  type="password"
                  required
                  placeholder="Tối thiểu 8 ký tự"
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Xác Nhận Mật Khẩu Mới
                </label>
                <input
                  type="password"
                  required
                  placeholder="Nhập lại mật khẩu mới"
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>

              <button
                type="submit"
                disabled={changePwdLoading}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300 text-sm"
              >
                {changePwdLoading ? "Đang thay đổi..." : "Thay Đổi Mật Khẩu"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
