import { adminApi } from "../adminClient";

interface AdminReportListItem {
  id: string;
  report_code: string;
  target_type: string;
  report_type: string;
  status: string;
  status_label: string;
  reporter_email: string;
  created_at_display: string;
}

interface AdminReportDetail extends AdminReportListItem {
  reason: string;
  admin_note: string | null;
  resolved_at: string | null;
  place_public_id: number | null;
  target_preview: Record<string, unknown> | null;
}

interface PaginatedReports {
  data: AdminReportListItem[];
  meta: { page: number; page_size: number; total: number };
}

export const adminReportsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return adminApi.get<PaginatedReports>(`/admin/reports${qs}`);
  },

  detail: (id: string) => adminApi.get<AdminReportDetail>(`/admin/reports/${id}`),

  updateStatus: (id: string, data: { status: string; admin_note?: string }) =>
    adminApi.patch<AdminReportDetail>(`/admin/reports/${id}`, data),

  executeAction: (id: string, action: string, reason: string) =>
    adminApi.post(`/admin/reports/${id}/action`, { action, reason }),
};

export type { AdminReportListItem, AdminReportDetail, PaginatedReports };
