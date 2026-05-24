import React, { useEffect, useState, useCallback } from "react";
import { reportsApi, MyReportItem } from "../../api/reports";
import { AlertTriangle, Loader, Calendar, CheckCircle, Clock } from "lucide-react";

export const MyReportsPage: React.FC = () => {
  const [reports, setReports] = useState<MyReportItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadMyReports = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await reportsApi.getMyReports(p);
      if (res.success && res.data) {
        setReports(res.data.data);
        setTotal(res.data.meta.total);
        setPage(res.data.meta.page);
      }
    } catch (err) {
      console.error("Error loading my reports", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMyReports(1);
  }, [loadMyReports]);

  const getStatusBadge = (statusLabel: string) => {
    const label = statusLabel.toLowerCase();
    if (label.includes("mới") || label.includes("new")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
          <Clock className="w-3.5 h-3.5" />
          {statusLabel}
        </span>
      );
    } else if (label.includes("đang xử lý") || label.includes("in_progress")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
          <Loader className="w-3.5 h-3.5 animate-spin" />
          {statusLabel}
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-50 text-green-700 border border-green-100">
          <CheckCircle className="w-3.5 h-3.5" />
          {statusLabel}
        </span>
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-black text-gray-800 tracking-tight">Báo cáo vi phạm của tôi</h1>
          <p className="text-sm text-gray-500 mt-1">Theo dõi danh sách và tình trạng xử lý các báo cáo vi phạm do bạn gửi lên.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-500 font-medium">Đang tải danh sách báo cáo...</p>
            </div>
          ) : reports.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {reports.map((r) => (
                <div key={r.report_code} className="p-6 hover:bg-gray-50/20 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-extrabold text-blue-600">{r.report_code}</span>
                      <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-600 text-[10px] font-bold tracking-wider uppercase border border-gray-200">
                        {r.report_type_label}
                      </span>
                    </div>

                    <p className="text-sm font-semibold text-gray-800">{r.target_summary}</p>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-400 font-medium">
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {r.created_at_display}
                      </span>
                      <span className="capitalize">Đối tượng: {r.target_type === "place" ? "địa điểm" : "bình luận"}</span>
                    </div>
                  </div>

                  <div className="flex items-center self-end sm:self-center">
                    {getStatusBadge(r.status_label)}
                  </div>
                </div>
              ))}

              {total > 20 && (
                <div className="flex items-center justify-center gap-4 py-6 border-t border-gray-100 bg-gray-50/20">
                  <button
                    disabled={page === 1}
                    onClick={() => loadMyReports(page - 1)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                  >
                    Trước
                  </button>
                  <span className="text-xs text-gray-600 font-medium">
                    Trang {page} / {Math.ceil(total / 20)}
                  </span>
                  <button
                    disabled={page * 20 >= total}
                    onClick={() => loadMyReports(page + 1)}
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
              <h3 className="text-base font-bold text-gray-700 mb-1">Chưa gửi báo cáo nào</h3>
              <p className="text-sm text-gray-500">Lịch sử gửi báo cáo của bạn trống.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyReportsPage;
