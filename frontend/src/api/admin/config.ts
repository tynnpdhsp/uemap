import { adminApi } from "../adminClient";

interface MapConfig {
  default_center: { lat: number; lng: number } | null;
  default_zoom: number | null;
  geofence: Record<string, unknown> | null;
  cluster_radius: number | null;
}

interface EmailTemplate {
  subject: string;
  html_body: string;
  text_body: string;
}

interface EmailTemplates {
  activation: EmailTemplate | null;
  reset_password: EmailTemplate | null;
}

export const adminConfigApi = {
  getMapConfig: () => adminApi.get<MapConfig>("/admin/config/map"),

  updateMapConfig: (data: Partial<MapConfig>) =>
    adminApi.patch<MapConfig>("/admin/config/map", data),

  getEmailTemplates: () =>
    adminApi.get<EmailTemplates>("/admin/config/email-templates"),

  updateEmailTemplates: (data: Partial<EmailTemplates>) =>
    adminApi.patch<EmailTemplates>("/admin/config/email-templates", data),

  testEmail: (to_email: string) =>
    adminApi.post("/admin/config/test-email", { to_email }),
};

export type { MapConfig, EmailTemplate, EmailTemplates };
