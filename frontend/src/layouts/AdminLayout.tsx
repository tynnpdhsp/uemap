import React, { useState } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAdminAuth } from "../context/AdminAuthContext";
import {
  LayoutDashboard,
  FolderOpen,
  MapPin,
  MessageSquare,
  AlertTriangle,
  Users,
  Shield,
  ScrollText,
  Settings,
  LogOut,
  Menu,
  X,
  Mail,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/categories", label: "Danh mục", icon: FolderOpen },
  { to: "/admin/places", label: "Địa điểm", icon: MapPin },
  { to: "/admin/comments", label: "Bình luận", icon: MessageSquare },
  { to: "/admin/reports", label: "Báo cáo", icon: AlertTriangle },
  { to: "/admin/students", label: "Sinh viên", icon: Users },
  {
    to: "/admin/admins",
    label: "Quản trị viên",
    icon: Shield,
    systemOnly: true,
  },
  { to: "/admin/audit-logs", label: "Nhật ký", icon: ScrollText },
  { to: "/admin/config/map", label: "Cấu hình bản đồ", icon: Settings },
  { to: "/admin/config/email", label: "Cấu hình email", icon: Mail },
];

export const AdminLayout: React.FC = () => {
  const { admin, logout } = useAdminAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/admin/login");
  };

  const isActive = (to: string, end?: boolean) => {
    if (end) return location.pathname === to;
    return location.pathname.startsWith(to);
  };

  const filteredNav = NAV_ITEMS.filter(
    (item) => !item.systemOnly || admin?.is_system_admin,
  );

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between h-16 px-5 border-b border-gray-700/50">
        <Link to="/admin" className="flex items-center space-x-2">
          <span className="text-xl font-extrabold text-white tracking-tight">
            UE<span className="text-blue-400">Map</span>
          </span>
          <span className="text-[10px] font-bold text-gray-400 bg-gray-700/50 px-2 py-0.5 rounded-full uppercase tracking-wider">
            Admin
          </span>
        </Link>
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden text-gray-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {filteredNav.map((item) => {
          const active = isActive(item.to, item.end);
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                active
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20"
                  : "text-gray-300 hover:bg-gray-700/50 hover:text-white"
              }`}
            >
              <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-700/50">
        <div className="mb-3 px-1">
          <p className="text-xs font-bold text-gray-400 truncate">
            {admin?.display_name}
          </p>
          <p className="text-[10px] text-gray-500 truncate">
            @{admin?.username}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center justify-center gap-2 w-full rounded-xl border border-gray-600 bg-gray-700/30 px-4 py-2.5 text-sm font-bold text-gray-300 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30 transition"
        >
          <LogOut className="w-4 h-4" />
          Đăng xuất
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-gray-900">
        {sidebarContent}
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="relative w-64 h-full bg-gray-900">
            {sidebarContent}
          </aside>
        </div>
      )}

      <div className="flex-1 lg:pl-64">
        <header className="sticky top-0 z-40 flex items-center h-16 bg-white border-b border-gray-100 px-4 lg:px-8 shadow-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden mr-4 text-gray-500 hover:text-gray-700"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-gray-700 hidden sm:inline">
              {admin?.display_name}
            </span>
            {admin?.is_system_admin && (
              <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                System Admin
              </span>
            )}
          </div>
        </header>

        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
