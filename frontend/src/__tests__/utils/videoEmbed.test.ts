import {
  getFacebookEmbedUrl,
  getVideoEmbedUrl,
  getYoutubeEmbedUrl,
} from "../../utils/videoEmbed";

describe("videoEmbed utils", () => {
  it("parse URL YouTube watch", () => {
    expect(
      getYoutubeEmbedUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ).toBe("https://www.youtube.com/embed/dQw4w9WgXcQ");
  });

  it("parse URL youtu.be", () => {
    expect(getYoutubeEmbedUrl("https://youtu.be/abc123XYZ")).toBe(
      "https://www.youtube.com/embed/abc123XYZ",
    );
  });

  it("parse URL Facebook Watch", () => {
    const watchUrl = "https://www.facebook.com/watch?v=123456789";
    expect(getFacebookEmbedUrl(watchUrl)).toBe(
      `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(watchUrl)}&show_text=false&width=560`,
    );
  });

  it("từ chối URL Facebook không phải Watch", () => {
    expect(getFacebookEmbedUrl("https://www.facebook.com/page")).toBeNull();
  });

  it("getVideoEmbedUrl ưu tiên YouTube rồi Facebook", () => {
    expect(
      getVideoEmbedUrl("https://www.youtube.com/watch?v=test1234567"),
    ).toContain("youtube.com/embed");
    expect(getVideoEmbedUrl("https://www.facebook.com/watch?v=999")).toContain(
      "facebook.com/plugins/video.php",
    );
    expect(getVideoEmbedUrl("https://example.com/video")).toBeNull();
  });
});
