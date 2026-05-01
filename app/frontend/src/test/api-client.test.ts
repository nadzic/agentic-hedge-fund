import { beforeEach, describe, expect, it, vi } from "vitest";

const { getSessionMock } = vi.hoisted(() => ({
  getSessionMock: vi.fn(),
}));

vi.mock("../lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: getSessionMock,
    },
  }),
}));

import { API_BASE_URL, ApiError, apiPost } from "../lib/api/client";

describe("apiPost", () => {
  beforeEach(() => {
    getSessionMock.mockReset();
    vi.restoreAllMocks();
  });

  it("adds Authorization header when session token exists", async () => {
    getSessionMock.mockResolvedValue({
      data: { session: { access_token: "token-123" } },
      error: null,
    });

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    } as Response);

    const result = await apiPost<{ ok: boolean }>("/signals/analyze", { query: "test payload" });

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      `${API_BASE_URL}/signals/analyze`,
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer token-123",
        }),
      }),
    );
  });

  it("omits Authorization header when token fetch fails", async () => {
    getSessionMock.mockResolvedValue({
      data: { session: null },
      error: { message: "session unavailable" },
    });

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    } as Response);

    await apiPost<{ ok: boolean }>("/rag/query", { query: "market update" });

    const [, init] = fetchMock.mock.calls[0];
    const headers = (init as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("throws ApiError with parsed JSON payload on non-OK response", async () => {
    getSessionMock.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 429,
      text: async () => JSON.stringify({ detail: { code: "rate_limit_exceeded" } }),
    } as Response);

    await expect(apiPost("/signals/analyze", { query: "payload" })).rejects.toMatchObject({
      name: "ApiError",
      status: 429,
      payload: { detail: { code: "rate_limit_exceeded" } },
    });
  });

  it("throws ApiError with raw text payload when response is not JSON", async () => {
    getSessionMock.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => "Internal server error",
    } as Response);

    try {
      await apiPost("/signals/analyze", { query: "payload" });
      throw new Error("Expected ApiError");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      const apiError = error as ApiError;
      expect(apiError.status).toBe(500);
      expect(apiError.payload).toBe("Internal server error");
      expect(apiError.message).toContain("API error 500");
    }
  });
});
