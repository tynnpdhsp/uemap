import {
  areValidCoordinates,
  formatCoordinate,
  isValidLatitude,
  isValidLongitude,
  parseCoordinateInput,
} from "../../utils/coordinates";

describe("coordinates utils", () => {
  it("formatCoordinate làm tròn 6 chữ số thập phân", () => {
    expect(formatCoordinate(10.7628123)).toBe("10.762812");
  });

  it("parseCoordinateInput chấp nhận số hợp lệ", () => {
    expect(parseCoordinateInput("10.7628")).toBe(10.7628);
    expect(parseCoordinateInput(" 106.6824 ")).toBe(106.6824);
  });

  it("parseCoordinateInput từ chối giá trị không phải số", () => {
    expect(parseCoordinateInput("")).toBeNull();
    expect(parseCoordinateInput("abc")).toBeNull();
  });

  it("kiểm tra phạm vi vĩ độ và kinh độ", () => {
    expect(isValidLatitude(10.76)).toBe(true);
    expect(isValidLatitude(91)).toBe(false);
    expect(isValidLongitude(106.68)).toBe(true);
    expect(isValidLongitude(-181)).toBe(false);
  });

  it("areValidCoordinates yêu cầu cả hai tọa độ hợp lệ", () => {
    expect(areValidCoordinates(10.76, 106.68)).toBe(true);
    expect(areValidCoordinates(null, 106.68)).toBe(false);
    expect(areValidCoordinates(100, 106.68)).toBe(false);
  });
});
