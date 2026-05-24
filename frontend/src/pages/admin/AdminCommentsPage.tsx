import React, { useEffect, useState, useCallback } from "react";
import { adminCommentsApi, type AdminCommentItem } from "../../api/admin/comments";
import { getErrorMessage } from "../../utils/errorMessage";
import { Loader, MessageSquare, Trash2 } from "lucide-react";

export const AdminCommentsPage: React.FC = () => {
  const [comments, setComments] = useState<AdminCommentItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(p) };
      if (statusFilter) params.status = statusFilter;
      const res = await adminCommentsApi.list(params);
      if (res.success && res.data) {
        setComments(res.data.data);
        setTotal(res.data.meta.total);
        setPage(res.data.meta.page);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { load(1); }, [load]);

  const handleDelete = async () => {
    if (!deleteId || deleteReason.length < 10) {
      setErrorMsg("Lý do xóa phải tối thiểu 10 ký tự.");
      return;
    }
    setDeleting(true);
    setErrorMsg(null);
    try {
      await adminCommentsApi.softDelete(deleteId, deleteReason);
      setDeleteId(null);
      setDeleteReason("");
      load(page);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Xóa bình luận thất bại."));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">Bình luận</h1>
        <p className="text-sm text-gray-500 mt-1">Quản lý bình luận trên hệ thống</p>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Trạng thái:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="p-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tất cả</option>
              <option value="visible">Hiển thị</option>
              <option value="deleted">Đã xóa</option>
            </select>
          </div>
          <div className="text-xs text-gray-400 font-bold">Tổng số: {total}</div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
          </div>
        ) : comments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-6">Địa điểm</th>
                  <th className="py-4 px-6">Tác giả</th>
                  <th className="py-4 px-6">Nội dung</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6">Ngày tạo</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {comments.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50/30 transition-colors">
                    <td className="py-4 px-6 font-extrabold text-blue-600">#{c.place_public_id}</td>
                    <td className="py-4 px-6 font-semibold text-gray-800">{c.author_display_name}</td>
                    <td className="py-4 px-6 text-gray-600 max-w-xs truncate">{c.content}</td>
                    <td className="py-4 px-6">
                      {c.status === "visible" ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-50 text-green-700 border border-green-100">
                          Hiển thị
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-100">
                          Đã xóa
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-gray-400 text-xs">{c.created_at_display}</td>
                    <td className="py-4 px-6 text-right">
                      {c.status === "visible" && (
                        <button
                          onClick={() => setDeleteId(c.id)}
                          className="p-2 border border-gray-100 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition"
                          title="Xóa mềm"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
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
            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">Không có bình luận nào</h3>
          </div>
        )}
      </div>

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Xóa mềm bình luận</h3>
            {errorMsg && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">{errorMsg}</div>
            )}
            <label className="block text-sm font-semibold text-gray-700 mb-2">Lý do xóa (tối thiểu 10 ký tự)</label>
            <textarea
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
              rows={3}
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-lg bg-red-600 px-4 py-2.5 text-white font-bold hover:bg-red-700 transition disabled:opacity-50 text-sm"
              >
                {deleting ? "Đang xóa..." : "Xác nhận xóa"}
              </button>
              <button
                onClick={() => { setDeleteId(null); setDeleteReason(""); setErrorMsg(null); }}
                className="rounded-lg border border-gray-300 px-4 py-2.5 text-gray-700 font-bold hover:bg-gray-50 transition text-sm"
              >
                Hủy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCommentsPage;
