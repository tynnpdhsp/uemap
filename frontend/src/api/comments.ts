import { api } from "./client";
import type { PaginatedAPIResponse } from "./types";

export interface CommentItem {
  id: string;
  author_display_name: string;
  content: string;
  created_at_display: string;
  is_mine?: boolean;
}

export interface MyCommentItem {
  id: string;
  content: string;
  content_preview: string;
  place_name: string;
  place_public_id: number;
  status_label: string;
  created_at_display: string;
}

export const commentsApi = {
  getPlaceComments: (publicId: number, page = 1) =>
    api.get<CommentItem[]>(
      `/places/${publicId}/comments?page=${page}`,
    ) as Promise<PaginatedAPIResponse<CommentItem[]>>,

  createComment: (publicId: number, content: string) =>
    api.post<CommentItem>(`/places/${publicId}/comments`, { content }),

  updateComment: (commentId: string, content: string) =>
    api.patch<{ message: string }>(`/comments/${commentId}`, { content }),

  deleteComment: (commentId: string) =>
    api.delete<void>(`/comments/${commentId}`),

  getMyComments: (page = 1) =>
    api.get<MyCommentItem[]>(`/my/comments?page=${page}`) as Promise<
      PaginatedAPIResponse<MyCommentItem[]>
    >,
};
