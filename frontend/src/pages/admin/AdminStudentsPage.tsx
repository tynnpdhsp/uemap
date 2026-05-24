import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminStudentsApi,
  type AdminStudentListItem,
  type AdminStudentDetail,
} from "../../api/admin/students";
import { getErrorMessage } from "../../utils/errorMessage";
import { Loader, Users, Lock, Unlock, Eye, X } from "lucide-react";

export const AdminStudentsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [students, setStudents] = useState<AdminStudentListItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState(
    searchParams.get("status") || "",
  );
  const [emailSearch, setEmailSearch] = useState("");
  const [detail, setDetail] = useState<AdminStudentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [lockId, setLockId] = useState<string | null>(null);
  const [lockReason, setLockReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const params: Record<string, string> = { page: String(p) };
        if (statusFilter) params.status = statusFilter;
        if (emailSearch) params.email = emailSearch;
        const res = await adminStudentsApi.list(params);
        if (res.success && res.data) {
          setStudents(res.data.data);
          setTotal(res.data.meta.total);
          setPage(res.data.meta.page);
        }
      } catch {
        void 0;
      } finally {
        setLoading(false);
      }
    },
    [statusFilter, emailSearch],
  );

  useEffect(() => {
    load(1);
  }, [load]);

  const openDetail = async (id: string) => {
    setDetailLoading(true);
    setDetail(null);
    try {
      const res = await adminStudentsApi.detail(id);
      if (res.success) setDetail(res.data);
    } catch {
      void 0;
    } finally {
      setDetailLoading(false);
    }
  };

  const handleLock = async () => {
    if (!lockId || lockReason.length < 10) {
      setErrorMsg("Lý do khóa phải tối thiểu 10 ký tự.");
      return;
    }
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await adminStudentsApi.lock(lockId, lockReason);
      setLockId(null);
      setLockReason("");
      load(page);
      if (detail && detail.id === lockId) openDetail(lockId);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Khóa tài khoản thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnlock = async (id: string) => {
    setActionLoading(true);
    try {
      await adminStudentsApi.unlock(id);
      load(page);
      if (detail && detail.id === id) openDetail(id);
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Mở khóa thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string, label: string) => {
    const map: Record<string, string> = {
      active: "bg-green-50 text-green-700 border-green-100",
      locked: "bg-red-50 text-red-700 border-red-100",
      pending_activation: "bg-amber-50 text-amber-700 border-amber-100",
    };
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${map[status] || "bg-gray-50 text-gray-700 border-gray-100"}`}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">
          Sinh viên
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý tài khoản sinh viên trên hệ thống
        </p>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-4 flex-wrap">
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
                <option value="active">Đã kích hoạt</option>
                <option value="locked">Bị khóa</option>
                <option value="pending_activation">Chờ kích hoạt</option>
              </select>
            </div>
            <input
              type="text"
              placeholder="Tìm theo email..."
              className="p-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 w-56"
              value={emailSearch}
              onChange={(e) => setEmailSearch(e.target.value)}
            />
          </div>
          <div className="text-xs text-gray-400 font-bold">
            Tổng số: {total}
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
          </div>
        ) : students.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-6">Email</th>
                  <th className="py-4 px-6">Họ tên</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6">Ngày tạo</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {students.map((s) => (
                  <tr
                    key={s.id}
                    className="hover:bg-gray-50/30 transition-colors"
                  >
                    <td className="py-4 px-6 font-semibold text-gray-800">
                      {s.email}
                    </td>
                    <td className="py-4 px-6 text-gray-600">{s.full_name}</td>
                    <td className="py-4 px-6">
                      {getStatusBadge(s.status, s.status_label)}
                    </td>
                    <td className="py-4 px-6 text-gray-400 text-xs">
                      {s.created_at_display}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openDetail(s.id)}
                          className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-blue-600 transition"
                          title="Chi tiết"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {s.status === "active" && (
                          <button
                            onClick={() => setLockId(s.id)}
                            className="p-2 border border-gray-100 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition"
                            title="Khóa"
                          >
                            <Lock className="w-4 h-4" />
                          </button>
                        )}
                        {s.status === "locked" && (
                          <button
                            onClick={() => handleUnlock(s.id)}
                            disabled={actionLoading}
                            className="p-2 border border-gray-100 rounded-lg hover:bg-green-50 text-gray-600 hover:text-green-600 transition disabled:opacity-50"
                            title="Mở khóa"
                          >
                            <Unlock className="w-4 h-4" />
                          </button>
                        )}
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
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">
              Không có sinh viên nào
            </h3>
          </div>
        )}
      </div>

      {detail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 w-full max-w-lg mx-4 relative">
            <button
              onClick={() => setDetail(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
            {detailLoading ? (
              <div className="p-8 text-center">
                <Loader className="w-6 h-6 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : (
              <>
                <h3 className="text-lg font-bold text-gray-800 mb-4">
                  {detail.full_name}
                </h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="block text-xs font-semibold text-gray-400 uppercase">
                      Email
                    </span>
                    <span className="text-gray-900 font-medium">
                      {detail.email}
                    </span>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-gray-400 uppercase">
                      Trạng thái
                    </span>
                    {getStatusBadge(detail.status, detail.status_label)}
                  </div>
                  {detail.locked_reason && (
                    <div>
                      <span className="block text-xs font-semibold text-gray-400 uppercase">
                        Lý do khóa
                      </span>
                      <span className="text-red-600 font-medium">
                        {detail.locked_reason}
                      </span>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="block text-xs font-semibold text-gray-400 uppercase">
                        Số địa điểm
                      </span>
                      <span className="text-blue-600 font-bold">
                        {detail.places_count}
                      </span>
                    </div>
                    <div>
                      <span className="block text-xs font-semibold text-gray-400 uppercase">
                        Số bình luận
                      </span>
                      <span className="text-blue-600 font-bold">
                        {detail.comments_count}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-gray-400 uppercase">
                      Ngày kích hoạt
                    </span>
                    <span className="text-gray-900 font-medium">
                      {detail.activated_at_display || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-gray-400 uppercase">
                      Ngày tạo
                    </span>
                    <span className="text-gray-900 font-medium">
                      {detail.created_at_display}
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {lockId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-800 mb-4">
              Khóa tài khoản sinh viên
            </h3>
            {errorMsg && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
                {errorMsg}
              </div>
            )}
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Lý do khóa (tối thiểu 10 ký tự)
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
              rows={3}
              value={lockReason}
              onChange={(e) => setLockReason(e.target.value)}
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleLock}
                disabled={actionLoading}
                className="rounded-lg bg-red-600 px-4 py-2.5 text-white font-bold hover:bg-red-700 transition disabled:opacity-50 text-sm"
              >
                {actionLoading ? "Đang khóa..." : "Xác nhận khóa"}
              </button>
              <button
                onClick={() => {
                  setLockId(null);
                  setLockReason("");
                  setErrorMsg(null);
                }}
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

export default AdminStudentsPage;
