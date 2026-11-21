import { buildHistory, defaultProfile, defaultSettings } from "./mockData";
import type {
  AppApi,
  DemoState,
  DownloadInput,
  HistoryItem,
  HistoryPage,
  HistoryQuery,
  Platform,
  Preview,
  Profile,
  Settings,
  Stats,
} from "./types";
import { ApiError } from "./types";

const SETTINGS_KEY = "safi-miniapp-settings";

let items = buildHistory();
let profile: Profile = { ...defaultProfile };
let premium = false;

function readState(): DemoState | null {
  const search = new URLSearchParams(window.location.search).get("state");
  const hash = window.location.hash;
  const hashQuery = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  const fromHash = new URLSearchParams(hashQuery).get("state");
  const value = search || fromHash;
  if (value === "empty" || value === "error" || value === "loading") return value;
  return null;
}

function wait(): Promise<void> {
  const ms = 300 + Math.floor(Math.random() * 501);
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function gate(): Promise<void> {
  const state = readState();
  if (state === "loading") return new Promise(() => undefined);
  await wait();
  if (state === "error") throw new ApiError("network");
}

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return { ...defaultSettings };
    return { ...defaultSettings, ...(JSON.parse(raw) as Partial<Settings>) };
  } catch {
    return { ...defaultSettings };
  }
}

let settings = loadSettings();

function countsOf(list: HistoryItem[]): HistoryPage["counts"] {
  const counts: HistoryPage["counts"] = {
    all: list.length,
    instagram: 0,
    tiktok: 0,
    youtube: 0,
    facebook: 0,
  };
  for (const item of list) counts[item.platform] += 1;
  return counts;
}

function sourceItems(): HistoryItem[] {
  return readState() === "empty" ? [] : items;
}

export function detectPlatform(url: string): Platform | null {
  const value = url.trim().toLowerCase();
  if (!value) return null;
  if (value.includes("instagram.com") || value.includes("instagr.am")) return "instagram";
  if (value.includes("tiktok.com")) return "tiktok";
  if (value.includes("youtube.com") || value.includes("youtu.be")) return "youtube";
  if (value.includes("facebook.com") || value.includes("fb.watch") || value.includes("fb.com")) return "facebook";
  return null;
}

function statsFrom(list: HistoryItem[]): Stats {
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const byPlatform: Stats["byPlatform"] = { instagram: 0, tiktok: 0, youtube: 0, facebook: 0 };
  let sizeBytes = 0;
  let week = 0;
  for (const item of list) {
    byPlatform[item.platform] += 1;
    sizeBytes += item.sizeBytes;
    if (new Date(item.createdAt).getTime() >= weekAgo) week += 1;
  }
  return { total: list.length, week, sizeBytes, byPlatform };
}

export const mockApi: AppApi = {
  async getHistory(query: HistoryQuery): Promise<HistoryPage> {
    await gate();
    const list = sourceItems().filter((item) => {
      const platformOk = query.platform === "all" || item.platform === query.platform;
      const text = query.query.trim().toLowerCase();
      const textOk = !text || item.title.toLowerCase().includes(text) || item.author.toLowerCase().includes(text);
      return platformOk && textOk;
    });
    const sorted = [...list].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    const start = Math.max(0, (query.page - 1) * query.pageSize);
    return {
      items: sorted.slice(start, start + query.pageSize),
      total: sorted.length,
      counts: countsOf(
        sourceItems().filter((item) => {
          const text = query.query.trim().toLowerCase();
          return !text || item.title.toLowerCase().includes(text) || item.author.toLowerCase().includes(text);
        }),
      ),
    };
  },

  async getStats(): Promise<Stats> {
    await gate();
    return statsFrom(sourceItems());
  },

  async deleteItem(id: string): Promise<void> {
    await gate();
    items = items.filter((item) => item.id !== id);
  },

  async resendItem(id: string): Promise<void> {
    await gate();
    if (!items.some((item) => item.id === id)) throw new ApiError("invalid");
  },

  async getPreview(url: string): Promise<Preview> {
    await gate();
    const platform = detectPlatform(url);
    if (!platform) throw new ApiError("invalid");
    const sample = items.find((item) => item.platform === platform);
    return {
      platform,
      title: sample?.title ?? "Public video",
      author: sample?.author ?? "creator",
      durationSec: sample?.durationSec ?? 42,
      aspect: platform === "youtube" ? "16:9" : "9:16",
    };
  },

  async startDownload(input: DownloadInput): Promise<HistoryItem> {
    await gate();
    const platform = detectPlatform(input.url);
    if (!platform) throw new ApiError("invalid");
    const item: HistoryItem = {
      id: `new-${Date.now()}`,
      platform,
      title: input.format === "audio" ? "Audio extract" : "New download",
      author: "you",
      durationSec: 36,
      sizeBytes: input.format === "audio" ? 3_200_000 : 18_000_000,
      createdAt: new Date().toISOString(),
      sourceUrl: input.url,
      status: "success",
      aspect: platform === "youtube" ? "16:9" : "9:16",
    };
    items = [item, ...items];
    profile = { ...profile, dailyUsed: Math.min(profile.dailyLimit, profile.dailyUsed + 1) };
    return item;
  },

  async getProfile(): Promise<Profile> {
    await gate();
    return { ...profile, plan: premium ? "premium" : profile.plan };
  },

  async getSettings(): Promise<Settings> {
    await gate();
    return { ...settings };
  },

  async saveSettings(patch: Partial<Settings>): Promise<Settings> {
    await gate();
    settings = { ...settings, ...patch };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    return { ...settings };
  },

  async clearHistory(): Promise<void> {
    await gate();
    items = [];
  },

  async buyPremium(): Promise<void> {
    await gate();
    premium = true;
    profile = { ...profile, plan: "premium", dailyLimit: 100 };
  },
};
