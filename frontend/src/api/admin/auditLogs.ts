import { adminApi } from "../adminClient";

interface AuditLogItem {
  id: string;
  event_code: string;
  actor_role: string;
  actor_id: string | null;
  object_type: string;
  object_id: string | null;
  result: string;
  description: string;
  ip_address: string;
  occurred_at_display: string;
}

interface PaginatedAuditLogs {
  data: AuditLogItem[];
  meta: { page: number; page_size: number; total: number };
}

export const adminAuditLogsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return adminApi.get<PaginatedAuditLogs>(`/admin/audit-logs${qs}`);
  },

  exportCsv: () => adminApi.getBlob("/admin/audit-logs/export"),
};

export type { AuditLogItem, PaginatedAuditLogs };
