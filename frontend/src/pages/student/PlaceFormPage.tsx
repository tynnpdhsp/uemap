import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Marker,
  useMapEvents,
  useMap,
  Circle,
  Rectangle,
} from "react-leaflet";
import L from "leaflet";
import { mapApi, MapConfig, Category } from "../../api/map";
import { placesApi, PlaceCreatePayload } from "../../api/places";
import { uploadsApi } from "../../api/uploads";
import { getErrorMessage } from "../../utils/errorMessage";
import {
  areValidCoordinates,
  formatCoordinate,
  isValidLatitude,
  isValidLongitude,
  parseCoordinateInput,
} from "../../utils/coordinates";
import {
  MapPin,
  Image as ImageIcon,
  Video as VideoIcon,
  Save,
  Send,
  X,
  Loader,
  AlertTriangle,
  ChevronLeft,
  Link,
  Upload,
} from "lucide-react";

const getMarkerIcon = () => {
  return L.divIcon({
    html: `
      <div class="relative flex items-center justify-center">
        <span class="absolute inline-flex h-6 w-6 rounded-full bg-blue-500 opacity-60 animate-ping"></span>
        <span class="relative inline-flex h-4 w-4 rounded-full border-2 border-white shadow-md bg-blue-600"></span>
      </div>
    `,
    className: "custom-marker-pin",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const MapEventsHandler: React.FC<{
  onClick: (lat: number, lng: number) => void;
}> = ({ onClick }) => {
  useMapEvents({
    click(e) {
      onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

const MapViewSync: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true });
  }, [center, map]);
  return null;
};

export const PlaceFormPage: React.FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const isEditMode = !!publicId;

  const [categories, setCategories] = useState<Category[]>([]);
  const [config, setConfig] = useState<MapConfig | null>(null);

  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [scopeType, setScopeType] = useState("near_campus");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [latInput, setLatInput] = useState("");
  const [lngInput, setLngInput] = useState("");
  const [coordinateError, setCoordinateError] = useState<string | null>(null);
  const [hours, setHours] = useState("");
  const [contact, setContact] = useState("");

  const [imageFiles, setImageFiles] = useState<
    {
      file?: File;
      objectKey?: string;
      previewUrl: string;
      uploading: boolean;
    }[]
  >([]);
  const [videoKind, setVideoKind] = useState<"file" | "embed">("file");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoObjectKey, setVideoObjectKey] = useState<string | null>(null);
  const [videoUploadProgress, setVideoUploadProgress] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");

  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [fetchingDetails, setFetchingDetails] = useState(false);

  useEffect(() => {
    const loadConfigAndCategories = async () => {
      try {
        const configRes = await mapApi.getConfig();
        if (configRes.success && configRes.data) {
          setConfig(configRes.data);
          if (!isEditMode) {
            const defaultLat = configRes.data.default_center.lat;
            const defaultLng = configRes.data.default_center.lng;
            setLat(defaultLat);
            setLng(defaultLng);
            setLatInput(formatCoordinate(defaultLat));
            setLngInput(formatCoordinate(defaultLng));
          }
        }
        const catsRes = await mapApi.getCategories();
        if (catsRes.success && catsRes.data) {
          setCategories(catsRes.data);
          if (!isEditMode && catsRes.data.length > 0) {
            setCategoryId(catsRes.data[0].id);
          }
        }
      } catch (err) {
        console.error("Error loading config/categories", err);
      }
    };
    loadConfigAndCategories();
  }, [isEditMode]);

  useEffect(() => {
    const loadDetails = async () => {
      if (!isEditMode || !publicId) return;
      setFetchingDetails(true);
      try {
        const res = await placesApi.getMyPlaceDetail(parseInt(publicId, 10));
        if (res.success && res.data) {
          const d = res.data;
          setName(d.name);
          setCategoryId(d.category_id);
          setScopeType(d.scope_type);
          setDescription(d.description);
          setAddress(d.address);
          setLat(d.lat);
          setLng(d.lng);
          setLatInput(formatCoordinate(d.lat));
          setLngInput(formatCoordinate(d.lng));
          setHours(d.hours || "");
          setContact(d.contact || "");

          if (d.image_object_keys) {
            setImageFiles(
              d.image_object_keys.map((key) => ({
                objectKey: key,
                previewUrl: `/api/media/${key}`,
                uploading: false,
              })),
            );
          }

          if (d.video) {
            setVideoKind(d.video.kind);
            if (d.video.kind === "file") {
              setVideoObjectKey(d.video.object_key || null);
            } else {
              setVideoUrl(d.video.url || "");
            }
          }
        }
      } catch (err) {
        console.error("Error fetching place details", err);
        setSubmitError("Không thể tải thông tin địa điểm cần chỉnh sửa.");
      } finally {
        setFetchingDetails(false);
      }
    };
    loadDetails();
  }, [isEditMode, publicId]);

  const applyCoordinates = (newLat: number, newLng: number) => {
    setLat(newLat);
    setLng(newLng);
    setLatInput(formatCoordinate(newLat));
    setLngInput(formatCoordinate(newLng));
    setCoordinateError(null);
  };

  const handleMapClick = (clickLat: number, clickLng: number) => {
    applyCoordinates(
      parseFloat(clickLat.toFixed(6)),
      parseFloat(clickLng.toFixed(6)),
    );
  };

  const handleLatInputChange = (value: string) => {
    setLatInput(value);
    const parsed = parseCoordinateInput(value);
    if (parsed === null) {
      if (value.trim() === "") {
        setLat(null);
        setCoordinateError(null);
      } else {
        setCoordinateError("Vĩ độ phải là số từ -90 đến 90.");
      }
      return;
    }
    if (!isValidLatitude(parsed)) {
      setCoordinateError("Vĩ độ phải là số từ -90 đến 90.");
      return;
    }
    setLat(parsed);
    if (lng !== null && isValidLongitude(lng)) {
      setCoordinateError(null);
    }
  };

  const handleLngInputChange = (value: string) => {
    setLngInput(value);
    const parsed = parseCoordinateInput(value);
    if (parsed === null) {
      if (value.trim() === "") {
        setLng(null);
        setCoordinateError(null);
      } else {
        setCoordinateError("Kinh độ phải là số từ -180 đến 180.");
      }
      return;
    }
    if (!isValidLongitude(parsed)) {
      setCoordinateError("Kinh độ phải là số từ -180 đến 180.");
      return;
    }
    setLng(parsed);
    if (lat !== null && isValidLatitude(lat)) {
      setCoordinateError(null);
    }
  };

  const handleCoordinateBlur = () => {
    if (lat !== null && isValidLatitude(lat)) {
      setLatInput(formatCoordinate(lat));
    }
    if (lng !== null && isValidLongitude(lng)) {
      setLngInput(formatCoordinate(lng));
    }
  };

  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);

    if (imageFiles.length + files.length > 10) {
      alert("Bạn chỉ được phép tải lên tối đa 10 ảnh.");
      return;
    }

    const newImages = files.map((file) => {
      const previewUrl = URL.createObjectURL(file);
      return { file, previewUrl, uploading: true };
    });

    setImageFiles((prev) => [...prev, ...newImages]);

    for (let i = 0; i < newImages.length; i++) {
      const target = newImages[i];
      try {
        const res = await uploadsApi.uploadImages([target.file]);
        if (res.success && res.data.object_keys.length > 0) {
          const key = res.data.object_keys[0];
          const previewFromApi = res.data.preview_urls?.[0];
          setImageFiles((prev) =>
            prev.map((item) =>
              item.previewUrl === target.previewUrl
                ? {
                    ...item,
                    objectKey: key,
                    previewUrl: previewFromApi || item.previewUrl,
                    uploading: false,
                  }
                : item,
            ),
          );
        }
      } catch (err: unknown) {
        alert(getErrorMessage(err, `Lỗi tải lên ảnh ${target.file.name}`));
        setImageFiles((prev) =>
          prev.filter((item) => item.previewUrl !== target.previewUrl),
        );
      }
    }
  };

  const removeImage = (index: number) => {
    setImageFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleVideoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    setVideoFile(file);
    setVideoUploadProgress(true);
    setVideoObjectKey(null);

    try {
      const res = await uploadsApi.uploadVideo(file);
      if (res.success && res.data.object_key) {
        setVideoObjectKey(res.data.object_key);
      }
    } catch (err: unknown) {
      alert(getErrorMessage(err, "Lỗi tải lên video."));
      setVideoFile(null);
    } finally {
      setVideoUploadProgress(false);
    }
  };

  const handleSubmit = async (status: "draft" | "published") => {
    setSubmitError(null);
    if (!name || name.trim().length < 5) {
      setSubmitError("Tên địa điểm phải từ 5 ký tự.");
      return;
    }
    if (status === "published") {
      if (!description || description.trim().length < 20) {
        setSubmitError("Mô tả chi tiết phải từ 20 ký tự khi đăng công khai.");
        return;
      }
      if (!address || address.trim().length < 5) {
        setSubmitError("Địa chỉ phải từ 5 ký tự khi đăng công khai.");
        return;
      }
      if (!areValidCoordinates(lat, lng)) {
        setSubmitError(
          "Vui lòng chọn tọa độ trên bản đồ hoặc nhập vĩ độ/kinh độ hợp lệ.",
        );
        return;
      }
    }

    const uploadingImages = imageFiles.some((img) => img.uploading);
    if (uploadingImages) {
      setSubmitError("Vui lòng đợi quá trình tải ảnh lên hoàn tất.");
      return;
    }

    setLoading(true);

    const payload: PlaceCreatePayload = {
      name: name.trim(),
      category_id: categoryId,
      scope_type: scopeType,
      description: description.trim(),
      address: address.trim(),
      lat: lat ?? 10.7628,
      lng: lng ?? 106.6824,
      hours: hours.trim() || null,
      contact: contact.trim() || null,
      image_object_keys: imageFiles
        .map((img) => img.objectKey!)
        .filter(Boolean),
      video: null,
      status,
      ...(status === "published" ? { publish: true } : {}),
    };

    if (status === "draft") {
      payload.description = description.trim() || "";
      payload.address = address.trim() || "";
    }

    if (videoKind === "file" && videoObjectKey) {
      payload.video = {
        kind: "file",
        object_key: videoObjectKey,
        mime: videoFile?.type || "video/mp4",
      };
    } else if (videoKind === "embed" && videoUrl) {
      payload.video = {
        kind: "embed",
        url: videoUrl.trim(),
      };
    }

    try {
      if (isEditMode) {
        const res = await placesApi.update(parseInt(publicId, 10), payload);
        if (res.success) {
          navigate("/my/places");
        }
      } else {
        const res = await placesApi.create(payload);
        if (res.success) {
          navigate("/my/places");
        }
      }
    } catch (err: unknown) {
      setSubmitError(getErrorMessage(err, "Đã xảy ra lỗi khi lưu thông tin."));
    } finally {
      setLoading(false);
    }
  };

  if (fetchingDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="text-center animate-pulse">
          <Loader className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-500 font-medium">
            Đang tải thông tin địa điểm...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <button
          onClick={() => navigate("/my/places")}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-600 hover:text-blue-600 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          Quay lại quản lý địa điểm
        </button>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          <div className="p-8 border-b border-gray-100 bg-gradient-to-br from-blue-50/50 to-indigo-50/10">
            <h1 className="text-2xl font-black text-gray-800 tracking-tight flex items-center gap-2">
              <MapPin className="text-blue-600 w-6 h-6" />
              {isEditMode ? "Chỉnh sửa Địa điểm" : "Đăng ký Địa điểm mới"}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Điền các thông tin địa điểm của bạn. Lưu nháp nếu chưa sẵn sàng
              đăng công khai.
            </p>
          </div>

          <div className="p-8 space-y-6">
            {submitError && (
              <div className="p-4 bg-red-50 border border-red-100 text-red-700 text-sm rounded-2xl flex items-start gap-3 animate-shake">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-extrabold">Có lỗi xảy ra:</span>{" "}
                  {submitError}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Tên địa điểm *
                  </label>
                  <input
                    type="text"
                    placeholder="Ví dụ: Quán cơm tấm HCMUE ngon..."
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Danh mục *
                    </label>
                    <select
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Phạm vi *
                    </label>
                    <select
                      value={scopeType}
                      onChange={(e) => setScopeType(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="on_campus">Trong trường (Campus)</option>
                      <option value="near_campus">
                        Gần trường (Near Campus)
                      </option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Địa chỉ chi tiết *
                  </label>
                  <input
                    type="text"
                    placeholder="Số 280 An Dương Vương, Phường 4, Quận 5..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Giờ mở cửa (tùy chọn)
                    </label>
                    <input
                      type="text"
                      placeholder="Ví dụ: 07:00 - 22:00"
                      value={hours}
                      onChange={(e) => setHours(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Liên hệ (tùy chọn)
                    </label>
                    <input
                      type="text"
                      placeholder="SĐT, Facebook Link..."
                      value={contact}
                      onChange={(e) => setContact(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2 flex flex-col">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Tọa độ địa điểm *
                </label>
                <p className="text-[11px] text-gray-500">
                  Chọn trên bản đồ hoặc nhập vĩ độ/kinh độ (WGS84). Hai cách
                  nhập được đồng bộ tự động.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label
                      htmlFor="place-lat"
                      className="text-[10px] font-bold text-gray-400 uppercase"
                    >
                      Vĩ độ (lat)
                    </label>
                    <input
                      id="place-lat"
                      type="text"
                      inputMode="decimal"
                      placeholder="10.762800"
                      value={latInput}
                      onChange={(e) => handleLatInputChange(e.target.value)}
                      onBlur={handleCoordinateBlur}
                      className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div className="space-y-1">
                    <label
                      htmlFor="place-lng"
                      className="text-[10px] font-bold text-gray-400 uppercase"
                    >
                      Kinh độ (lng)
                    </label>
                    <input
                      id="place-lng"
                      type="text"
                      inputMode="decimal"
                      placeholder="106.682400"
                      value={lngInput}
                      onChange={(e) => handleLngInputChange(e.target.value)}
                      onBlur={handleCoordinateBlur}
                      className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {coordinateError && (
                  <p className="text-xs text-red-600 font-medium">
                    {coordinateError}
                  </p>
                )}

                <div className="flex-grow aspect-square rounded-2xl overflow-hidden border border-gray-200 relative min-h-[300px] shadow-sm">
                  {lat !== null && lng !== null ? (
                    <MapContainer
                      center={[lat, lng]}
                      zoom={16}
                      className="w-full h-full"
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <Marker position={[lat, lng]} icon={getMarkerIcon()} />
                      <MapViewSync center={[lat, lng]} />

                      {config &&
                        config.geofence &&
                        config.geofence.type === "rectangle" &&
                        config.geofence.bounds && (
                          <Rectangle
                            bounds={[
                              [
                                config.geofence.bounds.sw.lat,
                                config.geofence.bounds.sw.lng,
                              ],
                              [
                                config.geofence.bounds.ne.lat,
                                config.geofence.bounds.ne.lng,
                              ],
                            ]}
                            pathOptions={{
                              color: "#3b82f6",
                              weight: 1.5,
                              fillOpacity: 0.05,
                              dashArray: "5, 5",
                            }}
                          />
                        )}

                      {config &&
                        config.geofence &&
                        config.geofence.type === "radius" &&
                        config.geofence.center &&
                        config.geofence.radius_meters && (
                          <Circle
                            center={[
                              config.geofence.center.lat,
                              config.geofence.center.lng,
                            ]}
                            radius={config.geofence.radius_meters}
                            pathOptions={{
                              color: "#3b82f6",
                              weight: 1.5,
                              fillOpacity: 0.05,
                              dashArray: "5, 5",
                            }}
                          />
                        )}

                      <MapEventsHandler onClick={handleMapClick} />
                    </MapContainer>
                  ) : (
                    <div className="w-full h-full bg-gray-50 flex items-center justify-center text-xs text-gray-400">
                      Đang tải bản đồ...
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Mô tả chi tiết *
              </label>
              <textarea
                placeholder="Giới thiệu về địa điểm, giá cả, đánh giá cá nhân (tối thiểu 20 ký tự khi đăng)..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[120px]"
              />
            </div>

            <div className="space-y-3 p-6 bg-gray-50/50 rounded-2xl border border-gray-100">
              <h3 className="text-sm font-bold text-gray-800 flex items-center gap-1.5">
                <ImageIcon className="w-4 h-4 text-blue-600" />
                Album hình ảnh (Tối đa 10 ảnh, mỗi ảnh tối đa 5MB)
              </h3>
              <div className="flex flex-wrap gap-4 items-center">
                {imageFiles.map((img, idx) => (
                  <div
                    key={img.previewUrl}
                    className="relative w-24 aspect-square rounded-xl overflow-hidden border border-gray-200 group bg-white shadow-sm flex items-center justify-center"
                  >
                    {img.uploading ? (
                      <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center">
                        <Loader className="w-5 h-5 text-blue-600 animate-spin" />
                      </div>
                    ) : (
                      <>
                        <img
                          src={img.previewUrl}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                        <button
                          type="button"
                          onClick={() => removeImage(idx)}
                          className="absolute top-1 right-1 p-1 bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition shadow"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                ))}

                {imageFiles.length < 10 && (
                  <label className="w-24 aspect-square rounded-xl border-2 border-dashed border-gray-300 hover:border-blue-500 cursor-pointer flex flex-col items-center justify-center text-gray-400 hover:text-blue-500 transition bg-white shadow-sm">
                    <Upload className="w-5 h-5 mb-1" />
                    <span className="text-[10px] font-bold">Thêm ảnh</span>
                    <input
                      type="file"
                      multiple
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleImageChange}
                      className="hidden"
                    />
                  </label>
                )}
              </div>
            </div>

            <div className="space-y-4 p-6 bg-gray-50/50 rounded-2xl border border-gray-100">
              <h3 className="text-sm font-bold text-gray-800 flex items-center gap-1.5">
                <VideoIcon className="w-4 h-4 text-blue-600" />
                Video giới thiệu (Tùy chọn)
              </h3>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={videoKind === "file"}
                    onChange={() => setVideoKind("file")}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Tải tệp video lên
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={videoKind === "embed"}
                    onChange={() => setVideoKind("embed")}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Liên kết video nhúng
                  </span>
                </label>
              </div>

              {videoKind === "file" ? (
                <div className="flex items-center gap-4">
                  {videoFile ? (
                    <div className="flex items-center gap-3 bg-white px-4 py-2 border border-gray-200 rounded-xl shadow-sm text-sm">
                      <span className="font-medium text-gray-700 line-clamp-1">
                        {videoFile.name}
                      </span>
                      {videoUploadProgress ? (
                        <Loader className="w-4 h-4 text-blue-600 animate-spin" />
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            setVideoFile(null);
                            setVideoObjectKey(null);
                          }}
                          className="text-red-500 hover:text-red-700"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ) : (
                    <label className="inline-flex items-center gap-2 py-2.5 px-4 border border-gray-200 rounded-xl bg-white hover:bg-gray-50 text-gray-600 font-semibold cursor-pointer shadow-sm text-sm">
                      <Upload className="w-4 h-4" />
                      Chọn video (MP4/WebM &lt; 80MB)
                      <input
                        type="file"
                        accept="video/mp4,video/webm"
                        onChange={handleVideoChange}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Nhập đường dẫn Youtube, Facebook Watch..."
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
                  />
                  <Link className="absolute left-3 top-3 text-gray-400 w-4 h-4" />
                </div>
              )}
            </div>
          </div>

          <div className="p-8 border-t border-gray-100 bg-gray-50 flex flex-wrap gap-4 justify-end">
            <button
              onClick={() => handleSubmit("draft")}
              disabled={loading}
              className="px-6 py-3 bg-white border border-gray-200 text-gray-700 font-bold rounded-xl shadow-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 flex items-center gap-2 text-sm transition-all"
            >
              {loading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Lưu bản nháp
            </button>

            <button
              onClick={() => handleSubmit("published")}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 disabled:opacity-50 flex items-center gap-2 text-sm transition-all"
            >
              {loading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Đăng công khai
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaceFormPage;
