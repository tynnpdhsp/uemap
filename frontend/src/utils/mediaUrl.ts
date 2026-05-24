import type { PlaceDetailImage, PlaceDetailVideo } from "../api/places";

export function placeImageSrc(
  image: Pick<PlaceDetailImage, "url" | "object_key">,
): string {
  return image.url || `/api/media/${image.object_key}`;
}

export function placeVideoFileSrc(video: PlaceDetailVideo): string | null {
  if (video.kind !== "file") return null;
  return (
    video.url || (video.object_key ? `/api/media/${video.object_key}` : null)
  );
}
