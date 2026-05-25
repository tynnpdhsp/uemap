export function getYoutubeEmbedUrl(url: string): string | null {
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
}

export function getFacebookEmbedUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    if (!host.endsWith("facebook.com")) {
      return null;
    }
    if (!parsed.pathname.includes("/watch")) {
      return null;
    }
    return `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(url)}&show_text=false&width=560`;
  } catch {
    return null;
  }
}

export function getVideoEmbedUrl(url: string): string | null {
  return getYoutubeEmbedUrl(url) ?? getFacebookEmbedUrl(url);
}
