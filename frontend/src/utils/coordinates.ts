export function formatCoordinate(value: number): string {
  return value.toFixed(6);
}

export function parseCoordinateInput(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const num = Number(trimmed);
  if (!Number.isFinite(num)) {
    return null;
  }
  return num;
}

export function isValidLatitude(lat: number): boolean {
  return lat >= -90 && lat <= 90;
}

export function isValidLongitude(lng: number): boolean {
  return lng >= -180 && lng <= 180;
}

export function areValidCoordinates(
  lat: number | null,
  lng: number | null,
): boolean {
  return (
    lat !== null &&
    lng !== null &&
    isValidLatitude(lat) &&
    isValidLongitude(lng)
  );
}
