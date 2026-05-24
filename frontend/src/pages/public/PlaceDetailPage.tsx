import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { placesApi, PlaceDetail } from "../../api/places";
import { commentsApi, CommentItem } from "../../api/comments";
import { reportsApi, ReportCreatePayload } from "../../api/reports";
import {
  MapPin,
  Clock,
  Phone,
  AlertTriangle,
  Send,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  User,
  Play,
  Copy,
  Check,
} from "lucide-react";

export const PlaceDetailPage: React.FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, student } = useAuth();

  const [place, setPlace] = useState<PlaceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [comments, setComments] = useState<CommentItem[]>([]);
  const [commentPage, setCommentPage] = useState(1);
  const [commentTotal, setCommentTotal] = useState(0);
  const [commentLoading, setCommentLoading] = useState(false);
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  const [copied, setCopied] = useState(false);
  
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportTarget, setReportTarget] = useState<{ type: "place" | "comment"; id: string; summary: string } | null>(null);
  const [reportType, setReportType] = useState<ReportCreatePayload["report_type"]>("wrong_info");
  const [reportReason, setReportReason] = useState("");
  const [submittingReport, setSubmittingReport] = useState(false);
  const [reportSuccessCode, setReportSuccessCode] = useState<string | null>(null);

  const [activeImageIndex, setActiveImageIndex] = useState(0);

  const loadPlaceDetail = useCallback(async () => {
    if (!publicId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await placesApi.getDetail(parseInt(publicId, 10));
      if (res.success && res.data) {
        setPlace(res.data);
      } else {
        setError("Không tìm thấy địa điểm.");
      }
    } catch (err: any) {
      setError(err.message || "Đã xảy ra lỗi khi tải chi tiết địa điểm.");
    } finally {
      setLoading(false);
    }
  }, [publicId]);

  const loadComments = useCallback(async (page: number) => {
    if (!publicId) return;
    setCommentLoading(true);
    try {
      const res = await commentsApi.getPlaceComments(parseInt(publicId, 10), page);
      if (res.success && res.data) {
        setComments(res.data.data);
        setCommentTotal(res.data.meta.total);
        setCommentPage(res.data.meta.page);
      }
    } catch (err) {
      console.error("Error loading comments", err);
    } finally {
      setCommentLoading(false);
    }
  }, [publicId]);

  useEffect(() => {
    loadPlaceDetail();
    loadComments(1);
  }, [loadPlaceDetail, loadComments]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!publicId || newComment.trim().length < 10 || newComment.trim().length > 2000) return;
    setSubmittingComment(true);
    try {
      const res = await commentsApi.createComment(parseInt(publicId, 10), newComment.trim());
      if (res.success) {
        setNewComment("");
        loadComments(1);
      }
    } catch (err: any) {
      alert(err.message || "Không thể gửi bình luận.");
    } finally {
      setSubmittingComment(false);
    }
  };

  const openReportModal = (type: "place" | "comment", id: string, summary: string) => {
    setReportTarget({ type, id, summary });
    setReportType("wrong_info");
    setReportReason("");
    setReportSuccessCode(null);
    setReportModalOpen(true);
  };

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportTarget || reportReason.trim().length < 20 || reportReason.trim().length > 500) return;
    setSubmittingReport(true);
    try {
      const res = await reportsApi.create({
        target_type: reportTarget.type,
        target_id: reportTarget.id,
        report_type: reportType,
        reason: reportReason.trim(),
      });
      if (res.success && res.data) {
        setReportSuccessCode(res.data.report_code);
      }
    } catch (err: any) {
      alert(err.message || "Không thể gửi báo cáo.");
    } finally {
      setSubmittingReport(false);
    }
  };

  const getYoutubeEmbedUrl = (url: string) => {
    try {
      let videoId = "";
      if (url.includes("youtu.be/")) {
        videoId = url.split("youtu.be/")[1].split(/[?#]/)[0];
      } else if (url.includes("youtube.com/watch")) {
        const urlParams = new URLSearchParams(new URL(url).search);
        videoId = urlParams.get("v") || "";
      } else if (url.includes("youtube.com/embed/")) {
        videoId = url.split("youtube.com/embed/")[1].split(/[?#]/)[0];
      }
      return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 font-medium">Đang tải thông tin địa điểm...</p>
        </div>
      </div>
    );
  }

  if (error || !place) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white p-8 rounded-2xl shadow-md max-w-md w-full text-center border border-gray-100">
          <AlertTriangle className="text-red-500 w-12 h-12 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Đã xảy ra lỗi</h2>
          <p className="text-gray-600 text-sm mb-6">{error || "Địa điểm không tồn tại hoặc chưa được công khai."}</p>
          <button
            onClick={() => navigate("/")}
            className="w-full py-2.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition"
          >
            Quay lại Bản đồ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        <button
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-600 hover:text-blue-600 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          Quay lại bản đồ
        </button>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8">
            <div className="space-y-4">
              {place.images.length > 0 ? (
                <div className="space-y-4">
                  <div className="relative aspect-video bg-gray-100 rounded-2xl overflow-hidden border border-gray-100 group shadow-inner">
                    <img
                      src={`/api/media/${place.images[activeImageIndex].object_key}`}
                      alt={place.name}
                      className="w-full h-full object-cover group-hover:scale-[1.02] transition duration-500"
                    />
                    {place.images.length > 1 && (
                      <div className="absolute inset-x-4 bottom-4 flex justify-between pointer-events-none">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveImageIndex((prev) => (prev === 0 ? place.images.length - 1 : prev - 1));
                          }}
                          className="p-2 bg-white/90 backdrop-blur rounded-xl text-gray-800 pointer-events-auto hover:bg-white shadow"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveImageIndex((prev) => (prev === place.images.length - 1 ? 0 : prev + 1));
                          }}
                          className="p-2 bg-white/90 backdrop-blur rounded-xl text-gray-800 pointer-events-auto hover:bg-white shadow"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                  {place.images.length > 1 && (
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {place.images.map((img, idx) => (
                        <button
                          key={img.object_key}
                          onClick={() => setActiveImageIndex(idx)}
                          className={`w-20 aspect-video rounded-lg overflow-hidden border-2 flex-shrink-0 transition ${
                            idx === activeImageIndex ? "border-blue-600 shadow-md" : "border-transparent"
                          }`}
                        >
                          <img src={`/api/media/${img.object_key}`} alt="" className="w-full h-full object-cover" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="aspect-video bg-gray-50 rounded-2xl flex items-center justify-center border border-gray-100 text-gray-400">
                  <MapPin className="w-12 h-12" />
                </div>
              )}

              {place.video && (
                <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100">
                  <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5">
                    <Play className="w-4 h-4 text-blue-600" />
                    Video giới thiệu
                  </h3>
                  {place.video.kind === "embed" && place.video.url && getYoutubeEmbedUrl(place.video.url) ? (
                    <div className="aspect-video rounded-xl overflow-hidden shadow">
                      <iframe
                        src={getYoutubeEmbedUrl(place.video.url)!}
                        title="Video giới thiệu"
                        className="w-full h-full"
                        allowFullScreen
                      ></iframe>
                    </div>
                  ) : place.video.kind === "file" && place.video.object_key ? (
                    <div className="aspect-video rounded-xl overflow-hidden shadow bg-black">
                      <video
                        src={`/api/media/${place.video.object_key}`}
                        controls
                        className="w-full h-full"
                      ></video>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500">Đường dẫn video không hợp lệ.</p>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-lg border border-blue-100 shadow-sm">
                    {place.category_name}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-bold rounded-lg border border-gray-200 shadow-sm">
                    {place.scope_label}
                  </span>
                </div>

                <h1 className="text-2xl font-black text-gray-800 tracking-tight leading-tight">{place.name}</h1>

                <p className="text-gray-600 text-sm leading-relaxed bg-gray-50/50 p-4 rounded-2xl border border-gray-100 shadow-inner whitespace-pre-line">
                  {place.description}
                </p>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-start gap-2.5">
                    <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                    <span>{place.address}</span>
                  </div>
                  {place.hours && (
                    <div className="flex items-center gap-2.5">
                      <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span>{place.hours}</span>
                    </div>
                  )}
                  {place.contact && (
                    <div className="flex items-center gap-2.5">
                      <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span>{place.contact}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-6 border-t border-gray-100 flex flex-wrap gap-3">
                <button
                  onClick={handleShare}
                  className="flex-grow flex items-center justify-center gap-2 py-2.5 px-4 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors shadow-sm text-sm"
                >
                  {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                  {copied ? "Đã sao chép" : "Sao chép liên kết"}
                </button>

                {isAuthenticated && (
                  <button
                    onClick={() => openReportModal("place", String(place.public_id), place.name)}
                    className="flex-grow flex items-center justify-center gap-2 py-2.5 px-4 bg-red-50 text-red-700 border border-red-100 font-bold rounded-xl hover:bg-red-100/50 transition-colors shadow-sm text-sm"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    Báo cáo Vi phạm
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 space-y-6">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            Bình luận ({commentTotal})
          </h2>

          {isAuthenticated ? (
            student?.status === "active" ? (
              <form onSubmit={handleCommentSubmit} className="relative">
                <textarea
                  placeholder="Chia sẻ nhận xét của bạn về địa điểm này (từ 10 đến 2000 ký tự)..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all min-h-[100px] shadow-inner"
                />
                <button
                  type="submit"
                  disabled={submittingComment || newComment.trim().length < 10 || newComment.trim().length > 2000}
                  className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 transition-colors shadow"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <div className="p-4 bg-yellow-50 text-yellow-800 text-sm rounded-2xl border border-yellow-100">
                Tài khoản chưa được kích hoạt hoặc đã bị khóa. Vui lòng hoàn tất kích hoạt để gửi bình luận.
              </div>
            )
          ) : (
            <div className="p-4 bg-blue-50 text-blue-800 text-sm rounded-2xl border border-blue-100 text-center font-medium">
              Vui lòng{" "}
              <button onClick={() => navigate("/login")} className="underline font-bold text-blue-700 hover:text-blue-800">
                Đăng nhập
              </button>{" "}
              để gửi bình luận của bạn.
            </div>
          )}

          {commentLoading && comments.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">Đang tải danh sách bình luận...</p>
          ) : comments.length > 0 ? (
            <div className="space-y-4 pt-4 border-t border-gray-100">
              {comments.map((c) => (
                <div key={c.id} className="group p-4 bg-gray-50/50 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                          <User className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-gray-800">{c.author_display_name}</h4>
                          <span className="text-[10px] text-gray-400">{c.created_at_display}</span>
                        </div>
                      </div>
                      {isAuthenticated && (
                        <button
                          onClick={() => openReportModal("comment", c.id, c.content)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-red-500 hover:text-red-700 flex items-center gap-1 font-semibold"
                          title="Báo cáo bình luận"
                        >
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Báo cáo
                        </button>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 mt-3 whitespace-pre-line leading-relaxed">{c.content}</p>
                  </div>
                </div>
              ))}

              {commentTotal > 20 && (
                <div className="flex items-center justify-center gap-4 pt-4">
                  <button
                    disabled={commentPage === 1 || commentLoading}
                    onClick={() => loadComments(commentPage - 1)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50"
                  >
                    Trước
                  </button>
                  <span className="text-sm text-gray-600">
                    Trang {commentPage} / {Math.ceil(commentTotal / 20)}
                  </span>
                  <button
                    disabled={commentPage * 20 >= commentTotal || commentLoading}
                    onClick={() => loadComments(commentPage + 1)}
                    className="p-2 border border-gray-200 rounded-lg disabled:opacity-50 text-gray-600 hover:bg-gray-50"
                  >
                    Sau
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-6">Chưa có bình luận nào. Hãy là người đầu tiên chia sẻ cảm nghĩ!</p>
          )}
        </div>
      </div>

      {reportModalOpen && reportTarget && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-3xl p-6 w-full max-w-md border border-gray-100 shadow-2xl relative">
            <button
              onClick={() => setReportModalOpen(false)}
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 text-sm font-bold"
            >
              ✕
            </button>

            {reportSuccessCode ? (
              <div className="text-center py-6 space-y-4">
                <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                  <Check className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-gray-800">Gửi báo cáo thành công</h3>
                <p className="text-sm text-gray-600">
                  Mã báo cáo của bạn là: <span className="font-extrabold text-blue-600">{reportSuccessCode}</span>.
                  Bạn có thể theo dõi tiến độ xử lý tại mục báo cáo của tôi.
                </p>
                <button
                  onClick={() => setReportModalOpen(false)}
                  className="w-full py-2 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition"
                >
                  Đóng
                </button>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4">
                <h3 className="text-lg font-bold text-gray-800 flex items-center gap-1.5">
                  <AlertTriangle className="text-red-500 w-5 h-5" />
                  Báo cáo Vi phạm
                </h3>
                <p className="text-xs text-gray-500">
                  Báo cáo: <span className="font-semibold text-gray-700">"{reportTarget.summary.slice(0, 50)}..."</span>
                </p>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase">Lý do chính</label>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value as any)}
                    className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="wrong_info">Thông tin sai lệch</option>
                    <option value="inappropriate">Nội dung không phù hợp</option>
                    <option value="spam">Spam / Quảng cáo</option>
                    <option value="other">Lý do khác</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase">Chi tiết (20 - 500 ký tự)</label>
                  <textarea
                    placeholder="Mô tả chi tiết vi phạm tại đây..."
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px]"
                    required
                  />
                  <div className="flex justify-between text-[10px] text-gray-400">
                    <span>Yêu cầu tối thiểu 20 ký tự</span>
                    <span className={reportReason.trim().length < 20 || reportReason.trim().length > 500 ? "text-red-500" : "text-green-500"}>
                      {reportReason.trim().length}/500
                    </span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submittingReport || reportReason.trim().length < 20 || reportReason.trim().length > 500}
                  className="w-full py-2.5 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 disabled:bg-gray-200 disabled:text-gray-400 transition"
                >
                  {submittingReport ? "Đang gửi báo cáo..." : "Gửi Báo cáo"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlaceDetailPage;
