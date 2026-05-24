import React, { useEffect, useState, useCallback } from "react";
import { adminCategoriesApi, type CategoryItem } from "../../api/admin/categories";
import { getErrorMessage } from "../../utils/errorMessage";
import { Plus, Edit3, Trash2, EyeOff, Eye, Loader } from "lucide-react";

export const AdminCategoriesPage: React.FC = () => {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [color, setColor] = useState("#3B82F6");
  const [order, setOrder] = useState(0);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminCategoriesApi.list();
      if (res.success) setCategories(res.data);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const resetForm = () => {
    setFormOpen(false);
    setEditId(null);
    setName("");
    setColor("#3B82F6");
    setOrder(0);
    setErrorMsg(null);
  };

  const openCreate = () => {
    resetForm();
    setFormOpen(true);
  };

  const openEdit = (cat: CategoryItem) => {
    setEditId(cat.id);
    setName(cat.name);
    setColor(cat.color);
    setOrder(cat.order);
    setFormOpen(true);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      if (editId) {
        await adminCategoriesApi.update(editId, { name, color, order });
        setSuccessMsg("Cập nhật danh mục thành công.");
      } else {
        await adminCategoriesApi.create({ name, color, order });
        setSuccessMsg("Tạo danh mục thành công.");
      }
      resetForm();
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Thao tác thất bại."));
    } finally {
      setSaving(false);
    }
  };

  const handleToggleHide = async (cat: CategoryItem) => {
    try {
      await adminCategoriesApi.hide(cat.id, !cat.is_hidden);
      load();
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Thao tác thất bại."));
    }
  };

  const handleDelete = async (cat: CategoryItem) => {
    if (!window.confirm(`Xóa danh mục "${cat.name}"? Thao tác này không thể hoàn tác.`)) return;
    try {
      await adminCategoriesApi.remove(cat.id);
      setSuccessMsg("Đã xóa danh mục.");
      load();
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Không thể xóa danh mục."));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gray-800 tracking-tight">Danh mục</h1>
          <p className="text-sm text-gray-500 mt-1">Quản lý danh mục địa điểm trên hệ thống</p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Tạo danh mục
        </button>
      </div>

      {successMsg && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">{successMsg}</div>
      )}

      {formOpen && (
        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            {editId ? "Sửa danh mục" : "Tạo danh mục mới"}
          </h2>
          {errorMsg && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">{errorMsg}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700">Tên danh mục</label>
                <input
                  type="text"
                  required
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700">Màu sắc</label>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    type="color"
                    className="w-10 h-10 rounded-lg border border-gray-300 cursor-pointer"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                  />
                  <input
                    type="text"
                    className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700">Thứ tự</label>
                <input
                  type="number"
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={order}
                  onChange={(e) => setOrder(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300 text-sm"
              >
                {saving ? "Đang lưu..." : editId ? "Cập nhật" : "Tạo mới"}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="rounded-lg border border-gray-300 px-6 py-2.5 text-gray-700 font-bold hover:bg-gray-50 transition text-sm"
              >
                Hủy
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
          </div>
        ) : categories.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-6">Màu</th>
                  <th className="py-4 px-6">Tên danh mục</th>
                  <th className="py-4 px-6">Thứ tự</th>
                  <th className="py-4 px-6">Số địa điểm</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {categories.map((cat) => (
                  <tr key={cat.id} className="hover:bg-gray-50/30 transition-colors">
                    <td className="py-4 px-6">
                      <div className="w-6 h-6 rounded-full border border-gray-200" style={{ backgroundColor: cat.color }} />
                    </td>
                    <td className="py-4 px-6 font-semibold text-gray-800">{cat.name}</td>
                    <td className="py-4 px-6 text-gray-500">{cat.order}</td>
                    <td className="py-4 px-6 font-bold text-blue-600">{cat.place_count}</td>
                    <td className="py-4 px-6">
                      {cat.is_hidden ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-50 text-gray-600 border border-gray-100">
                          <EyeOff className="w-3.5 h-3.5" /> Đang ẩn
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-50 text-green-700 border border-green-100">
                          <Eye className="w-3.5 h-3.5" /> Hiển thị
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openEdit(cat)}
                          className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-indigo-600 transition"
                          title="Sửa"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleToggleHide(cat)}
                          className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-amber-600 transition"
                          title={cat.is_hidden ? "Hiển thị" : "Ẩn"}
                        >
                          {cat.is_hidden ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleDelete(cat)}
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
          </div>
        ) : (
          <div className="p-12 text-center">
            <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">Chưa có danh mục</h3>
          </div>
        )}
      </div>
    </div>
  );
};

const FolderOpen = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/></svg>
);

export default AdminCategoriesPage;
