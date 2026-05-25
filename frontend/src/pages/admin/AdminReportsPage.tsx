import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  adminReportsApi,
  type AdminReportListItem,
} from "../../api/admin/reports";
import { Loader, AlertTriangle, Eye } from "lucide-react";

export const AdminReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [reports, setReports] = useState<AdminReportListItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState(
    searchParams.get("status") || "",
  );

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const params: Record<string, string> = { page: String(p) };
        if (statusFilter) params.status = statusFilter;
        const res = await adminReportsApi.list(params);
        if (res.success && res.data) {
          setReports(res.data.data);
          setTotal(res.data.meta.total);
          setPage(res.data.meta.page);
        }
      } catch {
        void 0;
      } finally {
        setLoading(false);
      }
    },
    [statusFilter],
  );

  useEffect(() => {
    load(1);
  }, [load]);

  const getStatusBadge = (status: string, label: string) => {
    const map: Record<string, string> = {
      new: "bg-red-50 text-red-700 border-red-100",
      in_progress: "bg-amber-50 text-amber-700 border-amber-100",
      resolved: "bg-green-50 text-green-700 border-green-100",
    };
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${map[status] || map.new}`}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">
          Báo cáo vi phạm
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý các báo cáo vi phạm từ sinh viên
        </p>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Trạng thái:
            </span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="p-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả</option>
              <option value="new">Mới</option>
              <option value="in_progress">Đang xử lý</option>
              <option value="resolved">Đã giải quyết</option>
            </select>
          </div>
          <div className="text-xs text-gray-400 font-bold">
            Tổng số: {total}
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
          </div>
        ) : reports.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-6">Mã báo cáo</th>
                  <th className="py-4 px-6">Loại đối tượng</th>
                  <th className="py-4 px-6">Loại vi phạm</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6">Người báo cáo</th>
                  <th className="py-4 px-6">Ngày tạo</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {reports.map((r) => (
                  <tr
                    key={r.id}
                    className="hover:bg-gray-50/30 transition-colors"
                  >
                    <td className="py-4 px-6 font-extrabold text-blue-600">
                      {r.report_code}
                    </td>
                    <td className="py-4 px-6 text-gray-700">
                      {r.target_type === "place" ? "Địa điểm" : "Bình luận"}
                    </td>
                    <td className="py-4 px-6 text-gray-500">{r.report_type}</td>
                    <td className="py-4 px-6">
                      {getStatusBadge(r.status, r.status_label)}
                    </td>
                    <td className="py-4 px-6 text-gray-500 text-xs">
                      {r.reporter_email}
                    </td>
                    <td className="py-4 px-6 text-gray-400 text-xs">
                      {r.created_at_display}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => navigate(`/admin/reports/${r.id}`)}
                        className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-blue-600 transition"
                        title="Chi tiết"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {total > 20 && (
              <div className="flex items-center justify-center gap-4 py-6 border-t border-gray-100 bg-gray-50/20">
                <button
                  disabled={page === 1}
                  onClick={() => load(page - 1)}
                  className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                >
                  Trước
                </button>
                <span className="text-xs text-gray-600 font-medium">
                  Trang {page} / {Math.ceil(total / 20)}
                </span>
                <button
                  disabled={page * 20 >= total}
                  onClick={() => load(page + 1)}
                  className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                >
                  Sau
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="p-12 text-center">
            <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">
              Không có báo cáo nào
            </h3>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminReportsPage;
