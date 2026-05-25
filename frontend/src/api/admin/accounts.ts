import { adminApi } from "../adminClient";

interface AdminAccountItem {
  id: string;
  username: string;
  display_name: string;
  is_system_admin: boolean;
  status: string;
  status_label: string;
  last_login_at_display: string | null;
  created_at_display: string;
}

export const adminAccountsApi = {
  list: () => adminApi.get<AdminAccountItem[]>("/admin/admins"),

  create: (data: {
    username: string;
    password: string;
    display_name: string;
  }) => adminApi.post<AdminAccountItem>("/admin/admins", data),

  update: (id: string, data: { display_name?: string; password?: string }) =>
    adminApi.patch<AdminAccountItem>(`/admin/admins/${id}`, data),

  disable: (id: string) => adminApi.patch(`/admin/admins/${id}/disable`),
};

export type { AdminAccountItem };
