import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminDashboardApi,
  type DashboardStats,
} from "../../api/admin/dashboard";
import { AlertTriangle, Users, MapPin, Loader } from "lucide-react";

export const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await adminDashboardApi.getStats();
        if (res.success) setStats(res.data);
      } catch {
        void 0;
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  const cards = [
    {
      label: "Báo cáo mới",
      value: stats?.new_reports_count ?? 0,
      icon: AlertTriangle,
      color: "text-red-600 bg-red-50 border-red-100",
      iconColor: "text-red-500",
      link: "/admin/reports?status=new",
    },
    {
      label: "SV chưa kích hoạt (7 ngày)",
      value: stats?.pending_students_7d_count ?? 0,
      icon: Users,
      color: "text-amber-600 bg-amber-50 border-amber-100",
      iconColor: "text-amber-500",
      link: "/admin/students?status=pending_activation",
    },
    {
      label: "Địa điểm mới (7 ngày)",
      value: stats?.new_published_places_7d_count ?? 0,
      icon: MapPin,
      color: "text-green-600 bg-green-50 border-green-100",
      iconColor: "text-green-500",
      link: "/admin/places?status=published",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">
          Dashboard
        </h1>
        <p className="text-sm text-gray-500 mt-1">Tổng quan hệ thống</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <Link
            key={card.label}
            to={card.link}
            className={`rounded-2xl bg-white p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all group`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  {card.label}
                </p>
                <p className="text-3xl font-black text-gray-900 mt-2">
                  {card.value}
                </p>
              </div>
              <div
                className={`p-3 rounded-xl border ${card.color} group-hover:scale-110 transition-transform`}
              >
                <card.icon className={`w-6 h-6 ${card.iconColor}`} />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default AdminDashboardPage;
