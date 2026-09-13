import { describe, expect, it, vi } from "vitest";
import { parseSession } from "./auth";

function token(payload: object): string {
  return `header.${btoa(JSON.stringify(payload))}.signature`;
}

describe("parseSession", () => {
  it("accepts a non-expired token payload", () => {
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    expect(parseSession(token({ sub: "user-1", role: "employee", exp: 1767229200 })))
      .toEqual({ id: "user-1", role: "employee", exp: 1767229200 });
  });

  it("rejects expired or malformed tokens", () => {
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    expect(parseSession(token({ sub: "user-1", role: "employee", exp: 1 }))).toBeNull();
    expect(parseSession("bad-token")).toBeNull();
  });
});

