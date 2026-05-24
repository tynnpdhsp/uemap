export type MockFetchResult = {
  status?: number;
  body: unknown;
};

export type MockFetchHandler = (
  url: string,
  method: string,
  body?: unknown,
) => MockFetchResult | null;

export function installFetchMock(handler: MockFetchHandler) {
  const mock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    let parsedBody: unknown;
    if (init?.body && typeof init.body === "string") {
      parsedBody = JSON.parse(init.body) as unknown;
    }

    const result = handler(url, method, parsedBody);
    if (!result) {
      return {
        ok: false,
        status: 404,
        json: async () => ({
          success: false,
          error: { code: "NOT_MOCKED", message: `Chưa mock: ${method} ${url}`, details: [] },
        }),
      };
    }

    const status = result.status ?? 200;
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => result.body,
    };
  });

  global.fetch = mock as typeof fetch;
  return mock;
}

export function jsonOk<T>(data: T) {
  return { status: 200, body: { success: true, data } };
}

export function jsonError(message: string, status = 400) {
  return {
    status,
    body: {
      success: false,
      error: { code: "ERROR", message, details: [] },
    },
  };
}
