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
