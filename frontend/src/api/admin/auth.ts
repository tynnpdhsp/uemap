import { adminApi } from "../adminClient";

interface AdminInfo {
  id: string;
  username: string;
  display_name: string;
  is_system_admin: boolean;
  status: string;
  status_label: string;
  last_login_at_display: string | null;
}

interface LoginResponse {
  access_token: string;
  admin: AdminInfo;
}

export const adminAuthApi = {
  login: (username: string, password: string) =>
    adminApi.post<LoginResponse>("/admin/auth/login", { username, password }),

  logout: () => adminApi.post("/admin/auth/logout"),

  me: () => adminApi.get<AdminInfo>("/admin/auth/me"),
};

export type { AdminInfo, LoginResponse };
