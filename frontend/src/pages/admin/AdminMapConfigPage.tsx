import React, { useEffect, useState } from "react";
import { adminConfigApi, type MapConfig } from "../../api/admin/config";
import { getErrorMessage } from "../../utils/errorMessage";
import { Loader, Save } from "lucide-react";

export const AdminMapConfigPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [zoom, setZoom] = useState("");
  const [clusterRadius, setClusterRadius] = useState("");
  const [geofenceType, setGeofenceType] = useState("rectangle");
  const [swLat, setSwLat] = useState("");
  const [swLng, setSwLng] = useState("");
  const [neLat, setNeLat] = useState("");
  const [neLng, setNeLng] = useState("");
  const [rCenterLat, setRCenterLat] = useState("");
  const [rCenterLng, setRCenterLng] = useState("");
  const [radiusMeters, setRadiusMeters] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await adminConfigApi.getMapConfig();
      if (res.success && res.data) {
        setLat(res.data.default_center?.lat?.toString() || "");
        setLng(res.data.default_center?.lng?.toString() || "");
        setZoom(res.data.default_zoom?.toString() || "");
        setClusterRadius(res.data.cluster_radius?.toString() || "");
        const gf = res.data.geofence;
        if (gf && typeof gf === "object") {
          const type = typeof gf.type === "string" ? gf.type : "rectangle";
          setGeofenceType(type);
          if (
            type === "rectangle" &&
            gf.bounds &&
            typeof gf.bounds === "object"
          ) {
            const bounds = gf.bounds as {
              sw?: { lat?: number };
              ne?: { lat?: number; lng?: number };
            };
            setSwLat(bounds.sw?.lat?.toString() || "");
            setSwLng(
              (bounds.sw as { lng?: number } | undefined)?.lng?.toString() ||
                "",
            );
            setNeLat(bounds.ne?.lat?.toString() || "");
            setNeLng(bounds.ne?.lng?.toString() || "");
          } else if (
            type === "radius" &&
            gf.center &&
            typeof gf.center === "object"
          ) {
            const center = gf.center as { lat?: number; lng?: number };
            setRCenterLat(center.lat?.toString() || "");
            setRCenterLng(center.lng?.toString() || "");
            setRadiusMeters(
              typeof gf.radius_meters === "number"
                ? gf.radius_meters.toString()
                : "",
            );
          }
        }
      }
    } catch {
      void 0;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const data: Record<string, unknown> = {};
    if (lat && lng)
      data.default_center = { lat: parseFloat(lat), lng: parseFloat(lng) };
    if (zoom) data.default_zoom = parseInt(zoom);
    if (clusterRadius) data.cluster_radius = parseInt(clusterRadius);

    if (geofenceType === "rectangle") {
      data.geofence = {
        type: "rectangle",
        bounds: {
          sw: { lat: parseFloat(swLat), lng: parseFloat(swLng) },
          ne: { lat: parseFloat(neLat), lng: parseFloat(neLng) },
        },
      };
    } else {
      data.geofence = {
        type: "radius",
        center: { lat: parseFloat(rCenterLat), lng: parseFloat(rCenterLng) },
        radius_meters: parseFloat(radiusMeters),
      };
    }

    try {
      await adminConfigApi.updateMapConfig(data as Partial<MapConfig>);
      setSuccessMsg("Cập nhật cấu hình bản đồ thành công.");
      load();
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, "Cập nhật thất bại."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-black text-gray-800 tracking-tight">
          Cấu hình bản đồ
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Thiết lập tâm mặc định, zoom, geofence và cluster
        </p>
      </div>

      {successMsg && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm border border-green-100">
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-100">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            Tâm & Zoom mặc định
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Latitude
              </label>
              <input
                type="number"
                step="any"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Longitude
              </label>
              <input
                type="number"
                step="any"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                value={lng}
                onChange={(e) => setLng(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700">
                Zoom
              </label>
              <input
                type="number"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                value={zoom}
                onChange={(e) => setZoom(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-semibold text-gray-700">
              Cluster Radius
            </label>
            <input
              type="number"
              className="mt-1 w-40 rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
              value={clusterRadius}
              onChange={(e) => setClusterRadius(e.target.value)}
            />
          </div>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-md border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">
            Geofence
          </h2>
          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Loại geofence
            </label>
            <select
              value={geofenceType}
              onChange={(e) => setGeofenceType(e.target.value)}
              className="p-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="rectangle">Hình chữ nhật (Rectangle)</option>
              <option value="radius">Bán kính (Radius)</option>
            </select>
          </div>

          {geofenceType === "rectangle" && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  SW Lat
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={swLat}
                  onChange={(e) => setSwLat(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  SW Lng
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={swLng}
                  onChange={(e) => setSwLng(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  NE Lat
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={neLat}
                  onChange={(e) => setNeLat(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  NE Lng
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={neLng}
                  onChange={(e) => setNeLng(e.target.value)}
                />
              </div>
            </div>
          )}

          {geofenceType === "radius" && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  Center Lat
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={rCenterLat}
                  onChange={(e) => setRCenterLat(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  Center Lng
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={rCenterLng}
                  onChange={(e) => setRCenterLng(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                  Bán kính (m)
                </label>
                <input
                  type="number"
                  step="any"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  value={radiusMeters}
                  onChange={(e) => setRadiusMeters(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 transition disabled:bg-blue-300 text-sm"
        >
          <Save className="w-4 h-4" />
          {saving ? "Đang lưu..." : "Lưu cấu hình"}
        </button>
      </form>
    </div>
  );
};

export default AdminMapConfigPage;
