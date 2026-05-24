import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { commentsApi, MyCommentItem } from "../../api/comments";
import { Trash2, MessageSquare, ExternalLink, Loader, Calendar, MapPin } from "lucide-react";

export const MyCommentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [comments, setComments] = useState<MyCommentItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadMyComments = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await commentsApi.getMyComments(p);
      if (res.success && res.data) {
        setComments(res.data.data);
        setTotal(res.data.meta.total);
        setPage(res.data.meta.page);
      }
    } catch (err) {
      console.error("Error loading my comments", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMyComments(1);
  }, [loadMyComments]);

  const handleDelete = async (id: string) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa bình luận này? Thao tác này không thể hoàn tác.")) return;
    try {
      await commentsApi.deleteComment(id);
      loadMyComments(page);
    } catch (err: any) {
      alert(err.message || "Không thể xóa bình luận.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-black text-gray-800 tracking-tight">Bình luận của tôi</h1>
          <p className="text-sm text-gray-500 mt-1">Quản lý và xem lại lịch sử các bình luận của bạn trên các địa điểm.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-500 font-medium">Đang tải danh sách bình luận...</p>
            </div>
          ) : comments.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {comments.map((c) => (
                <div key={c.id} className="p-6 hover:bg-gray-50/20 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="space-y-2 max-w-2xl">
                    <p className="text-sm text-gray-700 italic leading-relaxed">"{c.content_preview}"</p>
                    
                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400 font-medium">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        Địa điểm: <span className="text-gray-700 font-bold">{c.place_name}</span>
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {c.created_at_display}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-green-50 text-green-700 border border-green-100 text-[10px] font-bold tracking-wider uppercase">
                        {c.status_label}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => navigate(`/places/${c.place_public_id}`)}
                      className="p-2 border border-gray-100 rounded-lg hover:bg-gray-50 text-gray-600 hover:text-blue-600 transition"
                      title="Xem địa điểm"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="p-2 border border-gray-100 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition"
                      title="Xóa bình luận"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}

              {total > 20 && (
                <div className="flex items-center justify-center gap-4 py-6 border-t border-gray-100 bg-gray-50/20">
                  <button
                    disabled={page === 1}
                    onClick={() => loadMyComments(page - 1)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                  >
                    Trước
                  </button>
                  <span className="text-xs text-gray-600 font-medium">
                    Trang {page} / {Math.ceil(total / 20)}
                  </span>
                  <button
                    disabled={page * 20 >= total}
                    onClick={() => loadMyComments(page + 1)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50 text-xs font-bold"
                  >
                    Sau
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center">
              <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-base font-bold text-gray-700 mb-1">Chưa có bình luận nào</h3>
              <p className="text-sm text-gray-500">Bạn chưa gửi bình luận nào trên hệ thống.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyCommentsPage;
