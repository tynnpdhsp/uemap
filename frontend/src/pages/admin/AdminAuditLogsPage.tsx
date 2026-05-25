import React, { useEffect, useState, useCallback } from "react";
import {
  adminAuditLogsApi,
  type AuditLogItem,
} from "../../api/admin/auditLogs";
import { getErrorMessage } from "../../utils/errorMessage";
import { Loader, ScrollText, Download } from "lucide-react";

export const AdminAuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [eventCodeFilter, setEventCodeFilter] = useState("");
  const [exporting, setExporting] = useState(false);

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const params: Record<string, string> = {
          page: String(p),
          page_size: "50",
        };
        if (eventCodeFilter) params.event_code = eventCodeFilter;
        const res = await adminAuditLogsApi.list(params);
        if (res.success && res.data) {
          setLogs(res.data.data);
          setTotal(res.data.meta.total);
          setPage(res.data.meta.page);
        }
      } catch {
        void 0;
      } finally {
        setLoading(false);
      }
    },
    [eventCodeFilter],
  );

  useEffect(() => {
    load(1);
  }, [load]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await adminAuditLogsApi.exportCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Xuất CSV thất bại."));
    } finally {
      setExporting(false);
    }
  };

  const getResultBadge = (result: string) => {
    if (result === "success") {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-50 text-green-700 border border-green-100">
          OK
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-50 text-red-700 border border-red-100">
        FAIL
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gray-800 tracking-tight">
            Nhật ký hệ thống
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Theo dõi các sự kiện và hoạt động trên hệ thống
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 transition-all text-sm disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          {exporting ? "Đang xuất..." : "Xuất CSV"}
        </button>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Mã sự kiện:
            </span>
            <input
              type="text"
              placeholder="e.g. ADMIN_LOGIN"
              className="p-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 w-44"
              value={eventCodeFilter}
              onChange={(e) => setEventCodeFilter(e.target.value)}
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
        ) : logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-50/20">
                  <th className="py-4 px-4">Thời gian</th>
                  <th className="py-4 px-4">Mã sự kiện</th>
                  <th className="py-4 px-4">Vai trò</th>
                  <th className="py-4 px-4">Kết quả</th>
                  <th className="py-4 px-4">Mô tả</th>
                  <th className="py-4 px-4">IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-xs">
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-gray-50/30 transition-colors"
                  >
                    <td className="py-3 px-4 text-gray-400 whitespace-nowrap">
                      {log.occurred_at_display}
                    </td>
                    <td className="py-3 px-4 font-bold text-gray-800">
                      {log.event_code}
                    </td>
                    <td className="py-3 px-4 text-gray-500">
                      {log.actor_role}
                    </td>
                    <td className="py-3 px-4">{getResultBadge(log.result)}</td>
                    <td className="py-3 px-4 text-gray-600 max-w-xs truncate">
                      {log.description}
                    </td>
                    <td className="py-3 px-4 text-gray-400 font-mono">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {total > 50 && (
              <div className="flex items-center justify-center gap-4 py-6 border-t border-gray-100 bg-gray-50/20">
                <button
                  disabled={page === 1}
                  onClick={() => load(page - 1)}
                  className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                >
                  Trước
                </button>
                <span className="text-xs text-gray-600 font-medium">
                  Trang {page} / {Math.ceil(total / 50)}
                </span>
                <button
                  disabled={page * 50 >= total}
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
            <ScrollText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-bold text-gray-700 mb-1">
              Chưa có nhật ký nào
            </h3>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminAuditLogsPage;
