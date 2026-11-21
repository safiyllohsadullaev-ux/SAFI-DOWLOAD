import type { AppApi, DownloadInput, HistoryQuery, Settings } from "./types";
import { ApiError } from "./types";

function initData(): string {
  return window.Telegram?.WebApp.initData ?? "";
}

const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": initData(),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError("network");
  }
  if (!response.ok) {
    throw new ApiError(response.status === 400 ? "invalid" : "network");
  }
  return (await response.json()) as T;
}

export const realApi: AppApi = {
  getHistory(query: HistoryQuery) {
    const params = new URLSearchParams({
      platform: query.platform,
      query: query.query,
      page: String(query.page),
      pageSize: String(query.pageSize),
    });
    return request(`/api/history?${params.toString()}`);
  },
  getStats() {
    return request("/api/stats");
  },
  deleteItem(id) {
    return request(`/api/history/${id}`, { method: "DELETE" });
  },
  resendItem(id) {
    return request(`/api/history/${id}/resend`, { method: "POST" });
  },
  getPreview(url) {
    return request("/api/preview", { method: "POST", body: JSON.stringify({ url }) });
  },
  startDownload(input: DownloadInput) {
    return request("/api/downloads", { method: "POST", body: JSON.stringify(input) });
  },
  getProfile() {
    return request("/api/profile");
  },
  getSettings() {
    return request("/api/settings");
  },
  saveSettings(patch: Partial<Settings>) {
    return request("/api/settings", { method: "POST", body: JSON.stringify(patch) });
  },
  clearHistory() {
    return request("/api/history", { method: "DELETE" });
  },
  buyPremium(stars) {
    return request("/api/premium", { method: "POST", body: JSON.stringify({ stars }) });
  },
};
