import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Circle,
  Rectangle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet.markercluster";
import { useAuth } from "../../context/AuthContext";
import { mapApi, MapConfig, Category } from "../../api/map";
import { placesApi, PlaceListItem, PlaceMarker } from "../../api/places";
import { readPaginatedList } from "../../api/types";
import {
  Search,
  MapPin,
  Layers,
  Plus,
  ChevronRight,
  ChevronLeft,
  Compass,
  List,
} from "lucide-react";

const LIST_PAGE_SIZE = 20;

interface ClusterMarkersProps {
  markers: PlaceMarker[];
  onMarkerClick: (place: PlaceMarker) => void;
}

const ClusterMarkers: React.FC<ClusterMarkersProps> = ({
  markers,
  onMarkerClick,
}) => {
  const map = useMap();
  const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);

  useEffect(() => {
    const clusterGroup = L.markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
      disableClusteringAtZoom: 17,
    });
    clusterGroupRef.current = clusterGroup;
    map.addLayer(clusterGroup);

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [map]);

  useEffect(() => {
    const clusterGroup = clusterGroupRef.current;
    if (!clusterGroup) return;

    clusterGroup.clearLayers();

    markers.forEach((m) => {
      const icon = L.divIcon({
        html: `
          <div class="relative flex items-center justify-center">
            <span class="absolute inline-flex h-6 w-6 rounded-full opacity-60 animate-ping" style="background-color: ${m.category_color}"></span>
            <span class="relative inline-flex h-4 w-4 rounded-full border-2 border-white shadow-md" style="background-color: ${m.category_color}"></span>
          </div>
        `,
        className: "custom-marker-pin",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([m.lat, m.lng], { icon });
      marker.on("click", () => {
        map.panTo([m.lat, m.lng]);
        onMarkerClick(m);
      });
      clusterGroup.addLayer(marker);
    });
  }, [markers, onMarkerClick, map]);

  return null;
};

interface FlyToLocationProps {
  center: [number, number] | null;
  zoom?: number;
}

const FlyToLocation: React.FC<FlyToLocationProps> = ({ center, zoom = 16 }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1.5 });
    }
  }, [center, zoom, map]);
  return null;
};

export const HomePage: React.FC = () => {
  const { isAuthenticated, student } = useAuth();
  const navigate = useNavigate();

  const [config, setConfig] = useState<MapConfig | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [allMarkers, setAllMarkers] = useState<PlaceMarker[]>([]);
  const [placeList, setPlaceList] = useState<PlaceListItem[]>([]);
  const [listPage, setListPage] = useState(1);
  const [listTotal, setListTotal] = useState(0);
  const [listSort, setListSort] = useState<"name_asc" | "updated_desc">(
    "name_asc",
  );
  const [listLoading, setListLoading] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<PlaceMarker | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(
    null,
  );
  const [mapCenter, setMapCenter] = useState<[number, number]>([
    10.7628, 106.6824,
  ]);
  const [mapZoom, setMapZoom] = useState(16);
  const [flyTarget, setFlyTarget] = useState<{
    center: [number, number];
    zoom: number;
  } | null>(null);

  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const loadConfigAndCategories = async () => {
      try {
        const configRes = await mapApi.getConfig();
        if (configRes.success && configRes.data) {
          setConfig(configRes.data);
          setMapCenter([
            configRes.data.default_center.lat,
            configRes.data.default_center.lng,
          ]);
          setMapZoom(configRes.data.default_zoom);
        }

        const catsRes = await mapApi.getCategories();
        if (catsRes.success && catsRes.data) {
          setCategories(catsRes.data);
          setSelectedCategoryIds(catsRes.data.map((c) => c.id));
        }
      } catch (err) {
        console.error("Error loading map config/categories", err);
      }
    };
    loadConfigAndCategories();
  }, []);

  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    debounceTimeoutRef.current = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  useEffect(() => {
    setListPage(1);
  }, [debouncedQuery, listSort, selectedCategoryIds]);

  const categoryFilter =
    selectedCategoryIds.length > 0 &&
    selectedCategoryIds.length < categories.length
      ? selectedCategoryIds
      : undefined;

  const isSearchActive = debouncedQuery.trim().length >= 2;

  const displayedMarkers = React.useMemo(() => {
    const q = debouncedQuery.trim().toLowerCase();
    if (q.length >= 2) {
      return allMarkers.filter(
        (m) =>
          m.name.toLowerCase().includes(q) ||
          m.address_short.toLowerCase().includes(q),
      );
    }
    return allMarkers;
  }, [allMarkers, debouncedQuery]);

  const loadMarkers = useCallback(async () => {
    try {
      const res = await placesApi.getMarkers({ category_ids: categoryFilter });
      if (res.success && res.data) {
        setAllMarkers(res.data);
      }
    } catch (err) {
      console.error("Error loading markers", err);
    }
  }, [categoryFilter]);

  const loadPlaceList = useCallback(async () => {
    setListLoading(true);
    try {
      const q = debouncedQuery.trim();
      const params: Parameters<typeof placesApi.list>[0] = {
        page: listPage,
        page_size: LIST_PAGE_SIZE,
        category_ids: categoryFilter,
        sort: listSort,
      };
      if (q.length >= 2) {
        params.q = q;
      }

      const res = await placesApi.list(params);
      const { items, meta } = readPaginatedList<PlaceListItem>(res);
      setPlaceList(items);
      setListTotal(meta?.total ?? items.length);
    } catch (err) {
      console.error("Error loading place list", err);
      setPlaceList([]);
      setListTotal(0);
    } finally {
      setListLoading(false);
    }
  }, [debouncedQuery, categoryFilter, listPage, listSort]);

  useEffect(() => {
    loadPlaceList();
  }, [loadPlaceList]);

  useEffect(() => {
    loadMarkers();
  }, [loadMarkers]);

  const handleCategoryToggle = (id: string) => {
    setSelectedCategoryIds((prev) =>
      prev.includes(id)
        ? prev.length === 1
          ? prev
          : prev.filter((x) => x !== id)
        : [...prev, id],
    );
  };

  const locateUser = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc: [number, number] = [
            position.coords.latitude,
            position.coords.longitude,
          ];
          setUserLocation(loc);
          setFlyTarget({ center: loc, zoom: 17 });
        },
        (err) => {
          console.error("Error obtaining geolocation", err);
        },
      );
    }
  };

  const handleMarkerClick = (place: PlaceMarker) => {
    setSelectedPlace(place);
  };

  const showOnMap = (publicId: number) => {
    const marker = allMarkers.find((m) => m.public_id === publicId);
    if (!marker) return;
    setFlyTarget({ center: [marker.lat, marker.lng], zoom: 17 });
    setSelectedPlace(marker);
  };

  const listTotalPages = Math.max(1, Math.ceil(listTotal / LIST_PAGE_SIZE));

  return (
    <div className="flex-grow flex flex-col lg:flex-row h-[calc(100vh-64px)] relative overflow-hidden bg-gray-50">
      <div className="w-full lg:w-96 bg-white border-r border-gray-200 flex flex-col z-20 shadow-xl lg:shadow-none">
        <div className="p-6 border-b border-gray-100 bg-gradient-to-br from-blue-50 to-indigo-50/30">
          <h1 className="text-xl font-bold text-gray-800 tracking-tight flex items-center gap-2">
            <MapPin className="text-blue-600 w-5 h-5 animate-pulse" />
            Bản đồ HCMUE
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Hệ sinh thái địa điểm học tập, ăn uống và tiện ích sinh viên
          </p>

          <div className="mt-4 relative">
            <input
              type="text"
              placeholder="Tìm kiếm địa điểm (từ 2 ký tự)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
            />
            <Search className="absolute left-3.5 top-2.5 text-gray-400 w-4 h-4" />
          </div>
        </div>

        <div className="flex-grow overflow-y-auto p-6 space-y-6">
          <div>
            <div className="flex items-center justify-between gap-2 mb-3">
              <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <List className="w-3.5 h-3.5" />
                {isSearchActive
                  ? `Kết quả tìm kiếm (${listTotal})`
                  : `Danh sách địa điểm (${listTotal})`}
              </h2>
              <select
                value={listSort}
                onChange={(e) =>
                  setListSort(e.target.value as "name_asc" | "updated_desc")
                }
                className="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Sắp xếp danh sách"
              >
                <option value="name_asc">Tên A-Z</option>
                <option value="updated_desc">Mới cập nhật</option>
              </select>
            </div>

            {listLoading ? (
              <p className="text-sm text-gray-500">Đang tải...</p>
            ) : placeList.length > 0 ? (
              <>
                <ul className="space-y-2">
                  {placeList.map((item) => (
                    <li
                      key={item.public_id}
                      className="p-3 rounded-xl border border-gray-100 bg-white hover:border-blue-200 hover:bg-blue-50/30 transition"
                    >
                      <button
                        type="button"
                        onClick={() => navigate(`/places/${item.public_id}`)}
                        className="w-full text-left"
                      >
                        <p className="text-sm font-semibold text-gray-800 line-clamp-1">
                          {item.name}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                          {item.address_short}
                        </p>
                        <p className="text-[10px] text-gray-400 mt-1">
                          {item.category_name} · {item.updated_at_display}
                        </p>
                      </button>
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={() => navigate(`/places/${item.public_id}`)}
                          className="flex-1 py-1.5 px-2 text-[11px] font-bold text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition"
                        >
                          Xem chi tiết
                        </button>
                        <button
                          type="button"
                          onClick={() => showOnMap(item.public_id)}
                          className="flex-1 py-1.5 px-2 text-[11px] font-bold text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition"
                        >
                          Hiện trên bản đồ
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>

                {listTotalPages > 1 && (
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <button
                      type="button"
                      disabled={listPage <= 1}
                      onClick={() => setListPage((p) => Math.max(1, p - 1))}
                      className="flex items-center gap-1 px-2 py-1.5 text-xs font-semibold text-gray-600 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      Trước
                    </button>
                    <span className="text-xs text-gray-500">
                      Trang {listPage} / {listTotalPages}
                    </span>
                    <button
                      type="button"
                      disabled={listPage >= listTotalPages}
                      onClick={() =>
                        setListPage((p) => Math.min(listTotalPages, p + 1))
                      }
                      className="flex items-center gap-1 px-2 py-1.5 text-xs font-semibold text-gray-600 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                    >
                      Sau
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500">
                {isSearchActive
                  ? "Không tìm thấy địa điểm phù hợp."
                  : "Chưa có địa điểm nào trong bộ lọc hiện tại."}
              </p>
            )}
          </div>

          <div>
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Lọc theo Danh mục
            </h2>
            <div className="space-y-2">
              {categories.map((c) => {
                const isActive = selectedCategoryIds.includes(c.id);
                return (
                  <button
                    key={c.id}
                    onClick={() => handleCategoryToggle(c.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-xl border transition-all text-left ${
                      isActive
                        ? "border-blue-100 bg-blue-50/50 shadow-sm"
                        : "border-gray-100 bg-white hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="w-3.5 h-3.5 rounded-full border border-white shadow-sm flex-shrink-0"
                        style={{ backgroundColor: c.color }}
                      ></span>
                      <span
                        className={`text-sm font-medium ${isActive ? "text-blue-900" : "text-gray-700"}`}
                      >
                        {c.name}
                      </span>
                    </div>
                    <div
                      className={`w-4 h-4 rounded-md border flex items-center justify-center transition-all ${
                        isActive
                          ? "bg-blue-600 border-blue-600 text-white"
                          : "border-gray-300 bg-white"
                      }`}
                    >
                      {isActive && (
                        <svg
                          className="w-2.5 h-2.5 fill-current"
                          viewBox="0 0 20 20"
                        >
                          <path d="M0 11l2-2 5 5L18 3l2 2L7 18z" />
                        </svg>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {isAuthenticated && (
            <button
              onClick={() => navigate("/my/places/new")}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:opacity-95 hover:shadow-xl transition-all"
            >
              <Plus className="w-5 h-5" />
              Đóng góp Địa điểm mới
            </button>
          )}
        </div>

        <div className="p-4 bg-gray-50 border-t border-gray-100 text-center">
          {isAuthenticated ? (
            <div className="text-xs text-gray-500">
              Sinh viên:{" "}
              <span className="font-bold text-gray-700">
                {student?.full_name}
              </span>
            </div>
          ) : (
            <button
              onClick={() => navigate("/login")}
              className="text-xs text-blue-600 font-bold hover:underline"
            >
              Đăng nhập để đóng góp vị trí
            </button>
          )}
        </div>
      </div>

      <div className="flex-grow h-full relative z-10">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          className="w-full h-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <ClusterMarkers
            markers={displayedMarkers}
            onMarkerClick={handleMarkerClick}
          />

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

          {userLocation && (
            <Circle
              center={userLocation}
              radius={10}
              pathOptions={{
                color: "#10b981",
                fillColor: "#10b981",
                fillOpacity: 0.5,
              }}
            />
          )}

          <FlyToLocation
            center={flyTarget?.center ?? null}
            zoom={flyTarget?.zoom ?? 16}
          />
        </MapContainer>

        <button
          onClick={locateUser}
          className="absolute right-6 top-6 z-20 p-3 bg-white rounded-xl shadow-lg border border-gray-100 text-gray-600 hover:text-blue-600 transition-colors flex items-center justify-center"
          title="Vị trí của tôi"
        >
          <Compass className="w-5 h-5 animate-spin-slow" />
        </button>

        {selectedPlace && (
          <div className="absolute left-6 right-6 bottom-6 lg:left-auto lg:right-6 lg:w-96 z-20 bg-white/95 backdrop-blur-md p-5 rounded-2xl shadow-2xl border border-gray-100 flex flex-col justify-between animate-slide-up">
            <div>
              <div className="flex items-start justify-between">
                <span
                  className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-white shadow-sm"
                  style={{ backgroundColor: selectedPlace.category_color }}
                >
                  Địa điểm
                </span>
                <button
                  onClick={() => setSelectedPlace(null)}
                  className="text-gray-400 hover:text-gray-600 text-sm font-bold"
                >
                  ✕
                </button>
              </div>
              <h3 className="text-base font-bold text-gray-800 mt-2 line-clamp-1">
                {selectedPlace.name}
              </h3>
              <p className="text-xs text-gray-500 mt-1 flex items-start gap-1">
                <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-gray-400 mt-0.5" />
                {selectedPlace.address_short}
              </p>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
              <button
                onClick={() => navigate(`/places/${selectedPlace.public_id}`)}
                className="flex-grow flex items-center justify-center gap-1 py-2 px-4 bg-blue-600 text-white text-xs font-bold rounded-lg shadow-md hover:bg-blue-700 transition-colors"
              >
                Xem chi tiết
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
