import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { placesApi, MyPlaceListItem } from "../../api/places";
import { Edit3, Trash2, Plus, ExternalLink, Loader, FileText, CheckCircle, EyeOff, AlertTriangle } from "lucide-react";

export const MyPlacesPage: React.FC = () => {
  const navigate = useNavigate();
  const [places, setPlaces] = useState<MyPlaceListItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  const loadMyPlaces = useCallback(async (p: number, status: string) => {
    setLoading(true);
    try {
      const res = await placesApi.getMyPlaces({ page: p, status: status || undefined });
      if (res.success && res.data) {
        setPlaces(res.data.data);
        setTotal(res.data.meta.total);
        setPage(res.data.meta.page);
      }
    } catch (err) {
      console.error("Error loading my places", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMyPlaces(1, statusFilter);
  }, [loadMyPlaces, statusFilter]);

  const handleDelete = async (publicId: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa địa điểm này? Thao tác này không thể hoàn tác.")) return;
    try {
      await placesApi.delete(publicId);
      loadMyPlaces(page, statusFilter);
    } catch (err: any) {
      alert(err.message || "Không thể xóa địa điểm.");
    }
  };

  const getStatusBadge = (status: MyPlaceListItem["status"], label: string) => {
    switch (status) {
      case "draft":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
            <FileText className="w-3.5 h-3.5" />
            {label}
          </span>
        );
      case "published":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-50 text-green-700 border border-green-100">
            <CheckCircle className="w-3.5 h-3.5" />
            {label}
          </span>
        );
      case "hidden":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-50 text-gray-700 border border-gray-100">
            <EyeOff className="w-3.5 h-3.5" />
            {label}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-100">
            <AlertTriangle className="w-3.5 h-3.5" />
            {label}
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-gray-800 tracking-tight">Địa điểm của tôi</h1>
            <p className="text-sm text-gray-500 mt-1">Danh sách các địa điểm bạn đã đăng ký hoặc lưu nháp trên hệ thống.</p>
          </div>
          <button
            onClick={() => navigate("/my/places/new")}
            className="inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 transition-all text-sm"
          >
            <Plus className="w-4 h-4" />
            Đóng góp địa điểm mới
          </button>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Lọc theo trạng thái:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="p-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tất cả</option>
                <option value="draft">Bản nháp</option>
                <option value="published">Đã đăng</option>
                <option value="hidden">Bị ẩn</option>
              </select>
            </div>
            <div className="text-xs text-gray-400 font-bold">Tổng số: {total}</div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-500 font-medium">Đang tải danh sách địa điểm...</p>
            </div>
          ) : places.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                    <th className="py-4 px-6">ID</th>
                    <th className="py-4 px-6">Tên địa điểm</th>
                    <th className="py-4 px-6">Trạng thái</th>
                    <th className="py-4 px-6 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-sm">
                  {places.map((p) => (
                    <tr key={p.public_id} className="hover:bg-gray-50/30 transition-colors">
                      <td className="py-4 px-6 font-extrabold text-blue-600">#{p.public_id}</td>
                      <td className="py-4 px-6 font-semibold text-gray-800">{p.name}</td>
                      <td className="py-4 px-6">{getStatusBadge(p.status, p.status_label)}</td>
                      <td className="py-4 px-6 text-right">
                        <div className="inline-flex gap-2">
                          {p.status === "published" && (
                            <button
                              onClick={() => navigate(`/places/${p.public_id}`)}
                              className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-blue-600 transition"
                              title="Xem trang công khai"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => navigate(`/my/places/${p.public_id}/edit`)}
                            className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-indigo-600 transition"
                            title="Sửa"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(p.public_id)}
                            className="p-2 border border-gray-100 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition"
                            title="Xóa"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {total > 20 && (
                <div className="flex items-center justify-center gap-4 py-6 border-t border-gray-100 bg-gray-50/20">
                  <button
                    disabled={page === 1}
                    onClick={() => loadMyPlaces(page - 1, statusFilter)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                  >
                    Trước
                  </button>
                  <span className="text-xs text-gray-600 font-medium">
                    Trang {page} / {Math.ceil(total / 20)}
                  </span>
                  <button
                    disabled={page * 20 >= total}
                    onClick={() => loadMyPlaces(page + 1, statusFilter)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                  >
                    Sau
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-base font-bold text-gray-700 mb-1">Chưa có địa điểm nào</h3>
              <p className="text-sm text-gray-500 mb-6">Bạn chưa tạo hoặc đăng ký địa điểm nào trên hệ thống.</p>
              <button
                onClick={() => navigate("/my/places/new")}
                className="py-2.5 px-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition"
              >
                Đăng ký Địa điểm đầu tiên
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyPlacesPage;
