import type { APIResponse } from "./client";

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
}

export type PaginatedAPIResponse<T> = APIResponse<T> & { meta: PageMeta };

/** Chuẩn API: `{ success, data: T[], meta }` — hỗ trợ mock test cũ bọc thêm một lớp `data`. */
export function readPaginatedList<T>(
  res: PaginatedAPIResponse<T[]> | APIResponse<unknown>,
): {
  items: T[];
  meta: PageMeta | null;
} {
  if (!res.success || res.data == null) {
    return { items: [], meta: null };
  }
  if (Array.isArray(res.data)) {
    return {
      items: res.data as T[],
      meta: (res as PaginatedAPIResponse<T[]>).meta ?? null,
    };
  }
  const nested = res.data as { data?: T[]; meta?: PageMeta };
  if (Array.isArray(nested.data)) {
    return {
      items: nested.data,
      meta: nested.meta ?? (res as PaginatedAPIResponse<T[]>).meta ?? null,
    };
  }
  return { items: [], meta: null };
}
