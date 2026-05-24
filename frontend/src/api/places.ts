import { api } from "./client";

export interface PlaceMarker {
  public_id: number;
  name: string;
  lat: number;
  lng: number;
  category_id: string;
  category_color: string;
  category_icon_url: string | null;
  address_short: string;
}

export interface PlaceListItem {
  public_id: number;
  name: string;
  category_name: string;
  address_short: string;
  updated_at_display: string;
}

export interface PlaceDetailImage {
  object_key: string;
  sort_order: number;
  mime: string;
}

export interface PlaceDetailVideo {
  kind: "file" | "embed";
  object_key?: string | null;
  mime?: string | null;
  url?: string | null;
}

export interface PlaceDetail {
  public_id: number;
  creator_student_id: string;
  creator_student_name: string;
  category_id: string;
  category_name: string;
  scope_type: string;
  scope_label: string;
  name: string;
  description: string;
  address: string;
  location: {
    type: "Point";
    coordinates: [number, number]; // [lng, lat]
  };
  hours: string | null;
  contact: string | null;
  images: PlaceDetailImage[];
  video: PlaceDetailVideo | null;
  updated_at_display: string;
}

export interface MyPlaceListItem {
  public_id: number;
  name: string;
  status: "draft" | "published" | "hidden" | "deleted";
  status_label: string;
  public_url: string | null;
}

export interface PlaceCreatePayload {
  name: string;
  category_id: string;
  scope_type: string;
  description: string;
  address: string;
  lat: number;
  lng: number;
  hours?: string | null;
  contact?: string | null;
  image_object_keys?: string[];
  video?: PlaceDetailVideo | null;
  status?: "draft" | "published";
}

export interface PlaceCreateResponse {
  public_id: number;
  status: string;
  status_label: string;
}

function buildQuery(params: Record<string, unknown>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null) {
      if (Array.isArray(val)) {
        val.forEach((v) => query.append(key, String(v)));
      } else {
        query.append(key, String(val));
      }
    }
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export const placesApi = {
  getMarkers: (filters: {
    category_ids?: string[];
    sw_lat?: number;
    sw_lng?: number;
    ne_lat?: number;
    ne_lng?: number;
  }) => api.get<PlaceMarker[]>(`/places/markers${buildQuery(filters)}`),

  getPlaces: (filters: {
    page?: number;
    page_size?: number;
    category_ids?: string[];
    q?: string;
    sort?: string;
  }) =>
    api.get<{
      data: PlaceListItem[];
      meta: { page: number; page_size: number; total: number };
    }>(`/places${buildQuery(filters)}`),

  getDetail: (publicId: number) => api.get<PlaceDetail>(`/places/${publicId}`),

  search: (filters: { q: string; category_ids?: string[]; page?: number }) =>
    api.get<{
      data: PlaceListItem[];
      meta: { page: number; page_size: number; total: number };
    }>(`/search${buildQuery(filters)}`),

  getMyPlaces: (filters: { page?: number; status?: string }) =>
    api.get<{
      data: MyPlaceListItem[];
      meta: { page: number; page_size: number; total: number };
    }>(`/my/places${buildQuery(filters)}`),

  getMyPlaceDetail: (publicId: number) =>
    api.get<PlaceCreatePayload & { public_id: number }>(`/my/places/${publicId}`),

  create: (payload: PlaceCreatePayload) =>
    api.post<PlaceCreateResponse>("/my/places", payload),

  update: (publicId: number, payload: PlaceCreatePayload) =>
    api.patch<PlaceCreateResponse>(`/my/places/${publicId}`, payload),

  delete: (publicId: number) => api.delete<void>(`/my/places/${publicId}`),
};
