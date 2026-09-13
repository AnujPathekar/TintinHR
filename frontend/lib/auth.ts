import type { Session } from "./types";

export function parseSession(token: string | null): Session | null {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    if (!payload.sub || !payload.role || payload.exp * 1000 <= Date.now()) return null;
    return { id: payload.sub, role: payload.role, exp: payload.exp };
  } catch {
    return null;
  }
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.assign("/login");
}
