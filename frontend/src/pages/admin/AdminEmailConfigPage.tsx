import React, { useEffect, useState } from "react";
import { adminConfigApi } from "../../api/admin/config";
import { getErrorMessage } from "../../utils/errorMessage";
import { Loader, Save, Send } from "lucide-react";

export const AdminEmailConfigPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [actSubject, setActSubject] = useState("");
  const [actHtml, setActHtml] = useState("");
  const [actText, setActText] = useState("");
  const [resetSubject, setResetSubject] = useState("");
  const [resetHtml, setResetHtml] = useState("");
  const [resetText, setResetText] = useState("");
  const [testEmail, setTestEmail] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await adminConfigApi.getEmailTemplates();
      if (res.success && res.data) {
        const d = res.data;
        setActSubject(d.activation?.subject || "");
        setActHtml(d.activation?.html_body || "");
        setActText(d.activation?.text_body || "");
        setResetSubject(d.reset_password?.subject || "");
        setResetHtml(d.reset_password?.html_body || "");
        setResetText(d.reset_password?.text_body || "");
      }
    } catch {
      void 0;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await adminConfigApi.updateEmailTemplates({
        activation: {
          subject: actSubject,
          html_body: actHtml,
          text_body: actText,
        },
        reset_password: {
          subject: resetSubject,
          html_body: resetHtml,
          text_body: resetText,
        },
      });
      setSuccessMsg("Cập nhật mẫu email thành công.");
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Cập nhật thất bại."));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!testEmail) return;
    setTesting(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await adminConfigApi.testEmail(testEmail);
      setSuccessMsg("Đã gửi email thử nghiệm thành công.");
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Gửi email thử nghiệm thất bại."));
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">
          Cấu hình email
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Thiết lập mẫu email OTP kích hoạt và đặt lại mật khẩu
        </p>
      </div>

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

      <form onSubmit={handleSave} className="space-y-6">
        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            Mẫu kích hoạt tài khoản
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Biến hỗ trợ: {"{full_name}"}, {"{otp_code}"}
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Tiêu đề
              </label>
              <input
                type="text"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                value={actSubject}
                onChange={(e) => setActSubject(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                HTML Body
              </label>
              <textarea
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm font-mono"
                rows={4}
                value={actHtml}
                onChange={(e) => setActHtml(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Text Body
              </label>
              <textarea
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
                rows={3}
                value={actText}
                onChange={(e) => setActText(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            Mẫu đặt lại mật khẩu
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Biến hỗ trợ: {"{full_name}"}, {"{otp_code}"}
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Tiêu đề
              </label>
              <input
                type="text"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                value={resetSubject}
                onChange={(e) => setResetSubject(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                HTML Body
              </label>
              <textarea
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm font-mono"
                rows={4}
                value={resetHtml}
                onChange={(e) => setResetHtml(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Text Body
              </label>
              <textarea
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm"
                rows={3}
                value={resetText}
                onChange={(e) => setResetText(e.target.value)}
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300 text-sm"
        >
          <Save className="w-4 h-4" />
          {saving ? "Đang lưu..." : "Lưu mẫu email"}
        </button>
      </form>

      <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
          Gửi email thử nghiệm
        </h2>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-700">
              Email nhận
            </label>
            <input
              type="email"
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="admin@example.com"
            />
          </div>
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-bold text-blue-700 hover:bg-blue-100 transition disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            {testing ? "Đang gửi..." : "Gửi thử"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminEmailConfigPage;
