import React, { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { adminPlacesApi, type AdminPlaceDetail } from "../../api/admin/places";
import { getErrorMessage } from "../../utils/errorMessage";
import { ArrowLeft, EyeOff, Eye, Trash2, Loader } from "lucide-react";

export const AdminPlaceDetailPage: React.FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const [place, setPlace] = useState<AdminPlaceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [hideNote, setHideNote] = useState("");
  const [showHideForm, setShowHideForm] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminPlacesApi.detail(Number(publicId));
      if (res.success) setPlace(res.data);
    } catch {
      setErrorMsg("Không tìm thấy địa điểm.");
    } finally {
      setLoading(false);
    }
  }, [publicId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleHide = async () => {
    if (hideNote.length < 10) {
      setErrorMsg("Ghi chú nội bộ phải tối thiểu 10 ký tự.");
      return;
    }
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await adminPlacesApi.hide(Number(publicId), hideNote);
      setSuccessMsg("Đã ẩn địa điểm.");
      setShowHideForm(false);
      setHideNote("");
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Ẩn địa điểm thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnhide = async () => {
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await adminPlacesApi.unhide(Number(publicId));
      setSuccessMsg("Đã bỏ ẩn địa điểm.");
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Bỏ ẩn thất bại."));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !window.confirm("Xóa mềm địa điểm này? Thao tác này không thể hoàn tác.")
    )
      return;
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await adminPlacesApi.softDelete(Number(publicId));
      setSuccessMsg("Đã xóa mềm địa điểm.");
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Xóa thất bại."));
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

  if (!place) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-gray-700">
          Không tìm thấy địa điểm
        </h2>
        <button
          onClick={() => navigate("/admin/places")}
          className="mt-4 text-blue-600 font-semibold hover:underline"
        >
          Quay lại danh sách
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <button
        onClick={() => navigate("/admin/places")}
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
            #{place.public_id} — {place.name}
          </h1>
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${
              place.status === "published"
                ? "bg-green-50 text-green-700 border-green-100"
                : place.status === "hidden"
                  ? "bg-gray-100 text-gray-600 border-gray-200"
                  : place.status === "draft"
                    ? "bg-amber-50 text-amber-700 border-amber-100"
                    : "bg-red-50 text-red-700 border-red-100"
            }`}
          >
            {place.status_label}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-3">
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Danh mục
              </span>
              <span className="text-gray-900 font-medium">
                {place.category_name}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Địa chỉ
              </span>
              <span className="text-gray-900 font-medium">{place.address}</span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Tọa độ
              </span>
              <span className="text-gray-900 font-medium">
                {place.lat}, {place.lng}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Phạm vi
              </span>
              <span className="text-gray-900 font-medium">
                {place.scope_type}
              </span>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Người tạo
              </span>
              <span className="text-gray-900 font-medium">
                {place.creator_email}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Ngày tạo
              </span>
              <span className="text-gray-900 font-medium">
                {place.created_at_display}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold text-gray-400 uppercase">
                Cập nhật
              </span>
              <span className="text-gray-900 font-medium">
                {place.updated_at_display}
              </span>
            </div>
            {place.hidden_note && (
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase">
                  Ghi chú ẩn
                </span>
                <span className="text-red-600 font-medium">
                  {place.hidden_note}
                </span>
              </div>
            )}
          </div>
        </div>

        {place.description && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <span className="block text-xs font-semibold text-gray-400 uppercase mb-1">
              Mô tả
            </span>
            <p className="text-sm text-gray-700 whitespace-pre-line">
              {place.description}
            </p>
          </div>
        )}
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
          Thao tác
        </h2>
        <div className="flex flex-wrap gap-3">
          {place.status === "published" && (
            <button
              onClick={() => setShowHideForm(true)}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-bold text-amber-700 hover:bg-amber-100 transition disabled:opacity-50"
            >
              <EyeOff className="w-4 h-4" /> Ẩn địa điểm
            </button>
          )}
          {place.status === "hidden" && (
            <button
              onClick={handleUnhide}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2.5 text-sm font-bold text-green-700 hover:bg-green-100 transition disabled:opacity-50"
            >
              <Eye className="w-4 h-4" /> Bỏ ẩn
            </button>
          )}
          {place.status !== "deleted" && (
            <button
              onClick={handleDelete}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-bold text-red-600 hover:bg-red-100 transition disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" /> Xóa mềm
            </button>
          )}
        </div>

        {showHideForm && (
          <div className="mt-4 p-4 rounded-xl bg-amber-50/50 border border-amber-100">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Ghi chú nội bộ (tối thiểu 10 ký tự)
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
              rows={3}
              value={hideNote}
              onChange={(e) => setHideNote(e.target.value)}
            />
            <div className="flex gap-3 mt-3">
              <button
                onClick={handleHide}
                disabled={actionLoading}
                className="rounded-lg bg-amber-600 px-4 py-2 text-white font-bold hover:bg-amber-700 transition disabled:opacity-50 text-sm"
              >
                {actionLoading ? "Đang xử lý..." : "Xác nhận ẩn"}
              </button>
              <button
                onClick={() => {
                  setShowHideForm(false);
                  setHideNote("");
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

export default AdminPlaceDetailPage;
