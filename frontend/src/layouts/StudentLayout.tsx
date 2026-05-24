import React from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const StudentLayout: React.FC = () => {
  const { student, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header / Navbar */}
      <nav className="bg-white border-b border-gray-100 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <span className="text-2xl font-extrabold text-blue-600 tracking-tight">
                  UE<span className="text-gray-800">Map</span>
                </span>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/profile"
                    className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition"
                  >
                    Chào, {student?.full_name || "Sinh viên"}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-bold text-red-600 hover:bg-red-100 transition"
                  >
                    Đăng Xuất
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition"
                  >
                    Đăng Nhập
                  </Link>
                  <Link
                    to="/register"
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white hover:bg-blue-700 transition"
                  >
                    Đăng Ký
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-grow">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white text-center py-6 text-sm border-t border-gray-800">
        <p>
          &copy; {new Date().getFullYear()} Bản đồ Sinh viên Sư phạm (HCMUE).
          Bảo lưu mọi quyền.
        </p>
      </footer>
    </div>
  );
};

export default StudentLayout;
