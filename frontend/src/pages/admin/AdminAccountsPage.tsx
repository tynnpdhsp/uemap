import React, { useEffect, useState, useCallback } from "react";
import {
  adminAccountsApi,
  type AdminAccountItem,
} from "../../api/admin/accounts";
import { getErrorMessage } from "../../utils/errorMessage";
import { Plus, Edit3, Loader, Shield, UserX } from "lucide-react";

export const AdminAccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<AdminAccountItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminAccountsApi.list();
      if (res.success) setAccounts(res.data);
    } catch {
      void 0;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const resetForm = () => {
    setFormOpen(false);
    setEditId(null);
    setUsername("");
    setPassword("");
    setDisplayName("");
    setErrorMsg(null);
  };

  const openCreate = () => {
    resetForm();
    setFormOpen(true);
  };

  const openEdit = (a: AdminAccountItem) => {
    setEditId(a.id);
    setDisplayName(a.display_name);
    setUsername(a.username);
    setPassword("");
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
        const data: { display_name?: string; password?: string } = {};
        if (displayName) data.display_name = displayName;
        if (password) data.password = password;
        await adminAccountsApi.update(editId, data);
        setSuccessMsg("Cập nhật tài khoản thành công.");
      } else {
        await adminAccountsApi.create({
          username,
          password,
          display_name: displayName,
        });
        setSuccessMsg("Tạo tài khoản admin thành công.");
      }
      resetForm();
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Thao tác thất bại."));
    } finally {
      setSaving(false);
    }
  };

  const handleDisable = async (id: string, name: string) => {
    if (!window.confirm(`Vô hiệu hóa tài khoản "${name}"?`)) return;
    try {
      await adminAccountsApi.disable(id);
      setSuccessMsg("Đã vô hiệu hóa tài khoản.");
      load();
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Không thể vô hiệu hóa."));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gray-800 tracking-tight">
            Quản trị viên
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Quản lý tài khoản quản trị viên (chỉ System Admin)
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Tạo admin
        </button>
      </div>

      {successMsg && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
          {successMsg}
        </div>
      )}

      {formOpen && (
        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            {editId ? "Sửa tài khoản" : "Tạo tài khoản admin"}
          </h2>
          {errorMsg && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
              {errorMsg}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Tên đăng nhập
                </label>
                <input
                  type="text"
                  required={!editId}
                  disabled={!!editId}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition disabled:bg-gray-100 disabled:text-gray-500"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  {editId
                    ? "Mật khẩu mới (để trống nếu không đổi)"
                    : "Mật khẩu"}
                </label>
                <input
                  type="password"
                  required={!editId}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700">
                  Tên hiển thị
                </label>
                <input
                  type="text"
                  required
                  className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
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
        ) : accounts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-6">Tên đăng nhập</th>
                  <th className="py-4 px-6">Tên hiển thị</th>
                  <th className="py-4 px-6">Vai trò</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6">Đăng nhập cuối</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {accounts.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-gray-50/30 transition-colors"
                  >
                    <td className="py-4 px-6 font-semibold text-gray-800">
                      @{a.username}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {a.display_name}
                    </td>
                    <td className="py-4 px-6">
                      {a.is_system_admin ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
                          <Shield className="w-3.5 h-3.5" /> System Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-50 text-gray-600 border border-gray-100">
                          Admin
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      {a.status === "active" ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-50 text-green-700 border border-green-100">
                          Hoạt động
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-100">
                          Vô hiệu
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-gray-400 text-xs">
                      {a.last_login_at_display || "—"}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openEdit(a)}
                          className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-indigo-600 transition"
                          title="Sửa"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        {a.status === "active" && !a.is_system_admin && (
                          <button
                            onClick={() => handleDisable(a.id, a.username)}
                            className="p-2 border border-gray-100 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition"
                            title="Vô hiệu hóa"
                          >
                            <UserX className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <Shield className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">
              Chưa có tài khoản admin
            </h3>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminAccountsPage;
