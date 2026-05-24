import "@testing-library/jest-dom";

if (typeof globalThis.Request === "undefined") {
  class RequestPolyfill {
    url: string;
    method: string;

    constructor(input: string | URL, init: RequestInit = {}) {
      this.url = typeof input === "string" ? input : input.toString();
      this.method = init.method ?? "GET";
    }
  }

  globalThis.Request = RequestPolyfill as unknown as typeof Request;
}

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  jest.useRealTimers();
});

jest.mock("react-leaflet", () => ({
  MapContainer: ({ children }: any) => children,
  TileLayer: () => null,
  Circle: () => null,
  Rectangle: () => null,
  Marker: () => null,
  useMap: () => ({
    setView: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    addLayer: jest.fn(),
    removeLayer: jest.fn(),
    panTo: jest.fn(),
    flyTo: jest.fn(),
  }),
  useMapEvents: () => null,
}));

jest.mock("leaflet", () => {
  const Leaflet = {
    divIcon: jest.fn().mockReturnValue({}),
    markerClusterGroup: jest.fn().mockReturnValue({
      addLayer: jest.fn(),
      clearLayers: jest.fn(),
      on: jest.fn(),
    }),
    marker: jest.fn().mockReturnValue({
      on: jest.fn(),
    }),
    latLng: (lat: number, lng: number) => ({ lat, lng }),
    latLngBounds: () => ({
      extend: jest.fn(),
    }),
    icon: jest.fn().mockReturnValue({}),
  };
  return {
    __esModule: true,
    default: Leaflet,
    ...Leaflet,
  };
});

jest.mock("leaflet.markercluster", () => ({}));

