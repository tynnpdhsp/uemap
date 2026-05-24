import { adminApi } from "../adminClient";

interface CategoryItem {
  id: string;
  name: string;
  color: string;
  order: number;
  is_hidden: boolean;
  place_count: number;
  created_at_display: string;
}

export const adminCategoriesApi = {
  list: () => adminApi.get<CategoryItem[]>("/admin/categories"),

  create: (data: { name: string; color: string; order?: number }) =>
    adminApi.post<CategoryItem>("/admin/categories", data),

  update: (id: string, data: { name?: string; color?: string; order?: number }) =>
    adminApi.patch<CategoryItem>(`/admin/categories/${id}`, data),

  hide: (id: string, is_hidden: boolean) =>
    adminApi.patch<CategoryItem>(`/admin/categories/${id}/hide`, { is_hidden }),

  remove: (id: string) => adminApi.delete(`/admin/categories/${id}`),
};

export type { CategoryItem };
