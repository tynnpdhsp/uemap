import { api } from "./client";
import type { PaginatedAPIResponse } from "./types";

export interface ReportCreatePayload {
  target_type: "place" | "comment";
  target_id: string;
  report_type: "wrong_info" | "inappropriate" | "spam" | "other";
  reason: string;
}

export interface ReportCreateResponse {
  report_code: string;
  status: string;
  status_label: string;
  created_at_display: string;
}

export interface MyReportItem {
  report_code: string;
  target_type: "place" | "comment";
  target_summary: string;
  report_type_label: string;
  status_label: string;
  created_at_display: string;
}

export const reportsApi = {
  create: (payload: ReportCreatePayload) =>
    api.post<ReportCreateResponse>("/reports", payload),

  getMyReports: (page = 1) =>
    api.get<MyReportItem[]>(`/my/reports?page=${page}`) as Promise<
      PaginatedAPIResponse<MyReportItem[]>
    >,
};
