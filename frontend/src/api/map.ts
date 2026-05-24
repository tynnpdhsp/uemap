import { api } from "./client";

export interface GeofenceBounds {
  sw: { lat: number; lng: number };
  ne: { lat: number; lng: number };
}

export interface GeofenceConfig {
  type: "rectangle" | "radius";
  bounds?: GeofenceBounds;
  center?: { lat: number; lng: number };
  radius_meters?: number;
}

export interface MapConfig {
  default_center: { lat: number; lng: number };
  default_zoom: number;
  geofence: GeofenceConfig;
  cluster_zoom_threshold: number;
}

export interface Category {
  id: string;
  name: string;
  color: string;
  order: number;
  icon_url: string | null;
  description: string | null;
}

export const mapApi = {
  getConfig: () => api.get<MapConfig>("/config/map"),
  getCategories: () => api.get<Category[]>("/categories"),
};
