import { adminApi } from "../adminClient";

interface AdminPlaceListItem {
  public_id: number;
  name: string;
  category_name: string;
  status: string;
  status_label: string;
  creator_email: string;
  created_at_display: string;
}

interface AdminPlaceDetail {
  public_id: number;
  name: string;
  description: string;
  address: string;
  lat: number;
  lng: number;
  category_id: string;
  category_name: string;
  scope_type: string;
  status: string;
  status_label: string;
  hidden_note: string | null;
  creator_student_id: string;
  creator_email: string;
  images: string[];
  created_at_display: string;
  updated_at_display: string;
}

interface PaginatedList {
  data: AdminPlaceListItem[];
  meta: { page: number; page_size: number; total: number };
}

export const adminPlacesApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return adminApi.get<PaginatedList>(`/admin/places${qs}`);
  },

  detail: (publicId: number) =>
    adminApi.get<AdminPlaceDetail>(`/admin/places/${publicId}`),

  update: (publicId: number, data: Record<string, unknown>) =>
    adminApi.patch<AdminPlaceDetail>(`/admin/places/${publicId}`, data),

  hide: (publicId: number, hidden_note: string) =>
    adminApi.patch(`/admin/places/${publicId}/hide`, { hidden_note }),

  unhide: (publicId: number) =>
    adminApi.patch(`/admin/places/${publicId}/unhide`),

  softDelete: (publicId: number) =>
    adminApi.delete(`/admin/places/${publicId}`),

  transferCreator: (publicId: number, new_student_id: string) =>
    adminApi.patch(`/admin/places/${publicId}/transfer-creator`, { new_student_id }),
};

export type { AdminPlaceListItem, AdminPlaceDetail, PaginatedList };
