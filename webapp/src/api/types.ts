export type Platform = "instagram" | "tiktok" | "youtube" | "facebook";
export type ItemStatus = "success" | "error" | "progress";
export type MediaFormat = "video" | "audio";
export type VideoQuality = "360p" | "720p" | "1080p";
export type AudioQuality = "128kbps" | "320kbps";
export type Quality = VideoQuality | AudioQuality;
export type ThemeMode = "auto" | "light" | "dark";
export type Lang = "tg" | "ru" | "en";
export type Plan = "free" | "premium";
export type DemoState = "empty" | "error" | "loading";

export interface HistoryItem {
  id: string;
  platform: Platform;
  title: string;
  author: string;
  durationSec: number;
  sizeBytes: number;
  createdAt: string;
  sourceUrl: string;
  status: ItemStatus;
  progress?: number;
  aspect: "16:9" | "9:16";
}

export interface HistoryQuery {
  platform: Platform | "all";
  query: string;
  page: number;
  pageSize: number;
}

export interface HistoryPage {
  items: HistoryItem[];
  total: number;
  counts: Record<Platform | "all", number>;
}

export interface Profile {
  name: string;
  username: string;
  plan: Plan;
  dailyUsed: number;
  dailyLimit: number;
  invited: number;
  rewardDownloads: number;
  referralCode: string;
}

export interface Stats {
  total: number;
  week: number;
  sizeBytes: number;
  byPlatform: Record<Platform, number>;
}

export interface Preview {
  platform: Platform;
  title: string;
  author: string;
  durationSec: number;
  aspect: "16:9" | "9:16";
}

export interface Settings {
  language: Lang;
  theme: ThemeMode;
  defaultFormat: MediaFormat;
  defaultQuality: Quality;
  notifications: boolean;
}

export interface DownloadInput {
  url: string;
  format: MediaFormat;
  quality: Quality;
}

export interface AppApi {
  getHistory: (query: HistoryQuery) => Promise<HistoryPage>;
  getStats: () => Promise<Stats>;
  deleteItem: (id: string) => Promise<void>;
  resendItem: (id: string) => Promise<void>;
  getPreview: (url: string) => Promise<Preview>;
  startDownload: (input: DownloadInput) => Promise<HistoryItem>;
  getProfile: () => Promise<Profile>;
  getSettings: () => Promise<Settings>;
  saveSettings: (patch: Partial<Settings>) => Promise<Settings>;
  clearHistory: () => Promise<void>;
  buyPremium: (stars: number) => Promise<void>;
}

export class ApiError extends Error {
  code: "network" | "invalid";

  constructor(code: "network" | "invalid", message = code) {
    super(message);
    this.code = code;
  }
}
