import { adminApi } from "../adminClient";

interface AdminStudentListItem {
  id: string;
  email: string;
  full_name: string;
  status: string;
  status_label: string;
  created_at_display: string;
}

interface AdminStudentDetail extends AdminStudentListItem {
  locked_reason: string | null;
  activated_at_display: string | null;
  places_count: number;
  comments_count: number;
}

interface PaginatedStudents {
  data: AdminStudentListItem[];
  meta: { page: number; page_size: number; total: number };
}

export const adminStudentsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return adminApi.get<PaginatedStudents>(`/admin/students${qs}`);
  },

  detail: (id: string) => adminApi.get<AdminStudentDetail>(`/admin/students/${id}`),

  lock: (id: string, locked_reason: string) =>
    adminApi.patch<AdminStudentDetail>(`/admin/students/${id}/lock`, { locked_reason }),

  unlock: (id: string) =>
    adminApi.patch<AdminStudentDetail>(`/admin/students/${id}/unlock`),
};

export type { AdminStudentListItem, AdminStudentDetail, PaginatedStudents };
