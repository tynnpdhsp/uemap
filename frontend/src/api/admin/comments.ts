import { adminApi } from "../adminClient";

interface AdminCommentItem {
  id: string;
  place_public_id: number;
  author_display_name: string;
  content: string;
  status: string;
  admin_delete_reason: string | null;
  created_at_display: string;
}

interface PaginatedComments {
  data: AdminCommentItem[];
  meta: { page: number; page_size: number; total: number };
}

export const adminCommentsApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return adminApi.get<PaginatedComments>(`/admin/comments${qs}`);
  },

  softDelete: (id: string, admin_delete_reason: string) =>
    adminApi.delete(`/admin/comments/${id}`, { admin_delete_reason }),
};

export type { AdminCommentItem, PaginatedComments };
