import React, { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  adminReportsApi,
  type AdminReportDetail,
} from "../../api/admin/reports";
import { getErrorMessage } from "../../utils/errorMessage";
import {
  ArrowLeft,
  Loader,
  EyeOff,
  Trash2,
  Play,
  CheckCircle,
} from "lucide-react";

export const AdminReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<AdminReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [adminNote, setAdminNote] = useState("");
  const [actionReason, setActionReason] = useState("");
  const [showActionForm, setShowActionForm] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await adminReportsApi.detail(id);
      if (res.success) setReport(res.data);
    } catch {
      setErrorMsg("Không tìm thấy báo cáo.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleStatusUpdate = async (status: string) => {
    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const data: { status: string; admin_note?: string } = { status };
      if (status === "resolved") data.admin_note = adminNote;
      await adminReportsApi.updateStatus(id!, data);
      setSuccessMsg(
        `Đã cập nhật trạng thái thành ${status === "in_progress" ? "đang xử lý" : "đã giải quyết"}.`,
      );
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Cập nhật thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  const handleAction = async (action: string) => {
    if (actionReason.length < 10) {
      setErrorMsg("Lý do phải tối thiểu 10 ký tự.");
      return;
    }
    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await adminReportsApi.executeAction(id!, action, actionReason);
      setSuccessMsg("Đã thực hiện hành động thành công.");
      setShowActionForm(null);
      setActionReason("");
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Thực hiện hành động thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-gray-700">
          Không tìm thấy báo cáo
        </h2>
        <button
          onClick={() => navigate("/admin/reports")}
          className="mt-4 text-blue-600 font-semibold hover:underline"
        >
          Quay lại danh sách
        </button>
      </div>
    );
  }

  const statusBadge = (status: string, label: string) => {
    const map: Record<string, string> = {
      new: "bg-red-50 text-red-700 border-red-100",
      in_progress: "bg-amber-50 text-amber-700 border-amber-100",
      resolved: "bg-green-50 text-green-700 border-green-100",
    };
    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${map[status] || map.new}`}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <button
        onClick={() => navigate("/admin/reports")}
        className="inline-flex items-center gap-1 text-sm font-semibold text-gray-500 hover:text-blue-600 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Quay lại
      </button>

      {successMsg && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
          {errorMsg}
        </div>
      )}

      <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
          <h1 className="text-xl font-black text-gray-800">
            {report.report_code}
          </h1>
          {statusBadge(report.status, report.status_label)}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-3">
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Loại đối tượng
              </span>
              <span className="text-gray-900 font-medium">
                {report.target_type === "place" ? "Địa điểm" : "Bình luận"}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Loại vi phạm
              </span>
              <span className="text-gray-900 font-medium">
                {report.report_type}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Người báo cáo
              </span>
              <span className="text-gray-900 font-medium">
                {report.reporter_email}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Ngày tạo
              </span>
              <span className="text-gray-900 font-medium">
                {report.created_at_display}
              </span>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Lý do báo cáo
              </span>
              <p className="text-gray-700 whitespace-pre-line">
                {report.reason}
              </p>
            </div>
            {report.admin_note && (
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase">
                  Ghi chú admin
                </span>
                <p className="text-gray-700 whitespace-pre-line">
                  {report.admin_note}
                </p>
              </div>
            )}
            {report.resolved_at && (
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase">
                  Ngày giải quyết
                </span>
                <span className="text-gray-900 font-medium">
                  {report.resolved_at}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {report.status !== "resolved" && (
        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            Cập nhật trạng thái
          </h2>
          <div className="flex flex-wrap gap-3">
            {report.status === "new" && (
              <button
                onClick={() => handleStatusUpdate("in_progress")}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-bold text-amber-700 hover:bg-amber-100 transition disabled:opacity-50"
              >
                <Play className="w-4 h-4" /> Bắt đầu xử lý
              </button>
            )}
            {report.status === "in_progress" && (
              <div className="w-full space-y-3">
                <label className="block text-sm font-semibold text-gray-700">
                  Ghi chú giải quyết (bắt buộc)
                </label>
                <textarea
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
                  rows={3}
                  value={adminNote}
                  onChange={(e) => setAdminNote(e.target.value)}
                  placeholder="Nhập ghi chú về kết quả xử lý..."
                />
                <button
                  onClick={() => handleStatusUpdate("resolved")}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-white font-bold hover:bg-green-700 transition disabled:opacity-50 text-sm"
                >
                  <CheckCircle className="w-4 h-4" /> Đánh dấu đã giải quyết
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
          Hành động nhanh
        </h2>
        <div className="flex flex-wrap gap-3">
          {report.target_type === "place" && (
            <>
              <button
                onClick={() => setShowActionForm("hide_place")}
                className="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-bold text-amber-700 hover:bg-amber-100 transition"
              >
                <EyeOff className="w-4 h-4" /> Ẩn địa điểm
              </button>
              <button
                onClick={() => setShowActionForm("soft_delete_place")}
                className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-bold text-red-600 hover:bg-red-100 transition"
              >
                <Trash2 className="w-4 h-4" /> Xóa mềm địa điểm
              </button>
            </>
          )}
          {report.target_type === "comment" && (
            <button
              onClick={() => setShowActionForm("soft_delete_comment")}
              className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-bold text-red-600 hover:bg-red-100 transition"
            >
              <Trash2 className="w-4 h-4" /> Xóa mềm bình luận
            </button>
          )}
        </div>

        {showActionForm && (
          <div className="mt-4 p-4 rounded-xl bg-gray-50 border border-gray-200">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Lý do (tối thiểu 10 ký tự)
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
              rows={3}
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
            />
            <div className="flex gap-3 mt-3">
              <button
                onClick={() => handleAction(showActionForm)}
                disabled={actionLoading}
                className="rounded-lg bg-red-600 px-4 py-2 text-white font-bold hover:bg-red-700 transition disabled:opacity-50 text-sm"
              >
                {actionLoading ? "Đang xử lý..." : "Xác nhận"}
              </button>
              <button
                onClick={() => {
                  setShowActionForm(null);
                  setActionReason("");
                }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 font-bold hover:bg-gray-50 transition text-sm"
              >
                Hủy
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminReportDetailPage;
