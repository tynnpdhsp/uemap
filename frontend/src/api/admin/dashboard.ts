import { adminApi } from "../adminClient";

interface DashboardStats {
  new_reports_count: number;
  pending_students_7d_count: number;
  new_published_places_7d_count: number;
  links: Record<string, string>;
}

export const adminDashboardApi = {
  getStats: () => adminApi.get<DashboardStats>("/admin/dashboard/stats"),
};

export type { DashboardStats };
