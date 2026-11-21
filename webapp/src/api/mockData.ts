import type { HistoryItem, Platform, Profile, Settings } from "./types";

const hour = 60 * 60 * 1000;
const day = 24 * hour;

function at(offsetMs: number): string {
  return new Date(Date.now() - offsetMs).toISOString();
}

interface Seed {
  id: string;
  platform: Platform;
  title: string;
  author: string;
  durationSec: number;
  sizeBytes: number;
  ago: number;
  aspect: "16:9" | "9:16";
  status?: HistoryItem["status"];
  progress?: number;
}

const seeds: Seed[] = [
  { id: "ig-1", platform: "instagram", title: "Morning light on the rooftop", author: "safi.studio", durationSec: 15, sizeBytes: 4_200_000, ago: 25 * 60 * 1000, aspect: "9:16" },
  { id: "ig-2", platform: "instagram", title: "Reel: chai and rain", author: "dushanbe.daily", durationSec: 32, sizeBytes: 8_800_000, ago: 2 * hour, aspect: "9:16" },
  { id: "ig-3", platform: "instagram", title: "Carousel walk through the old city", author: "travel.tj", durationSec: 48, sizeBytes: 12_400_000, ago: 5 * hour, aspect: "9:16" },
  { id: "ig-4", platform: "instagram", title: "Kitchen notes, episode 4", author: "oshpaz", durationSec: 61, sizeBytes: 18_200_000, ago: 26 * hour, aspect: "9:16" },
  { id: "ig-5", platform: "instagram", title: "Studio setup in one minute", author: "safi.studio", durationSec: 58, sizeBytes: 15_600_000, ago: 3 * day, aspect: "9:16" },
  { id: "ig-6", platform: "instagram", title: "Friday market", author: "bazaar.cam", durationSec: 27, sizeBytes: 7_100_000, ago: 6 * day, aspect: "9:16" },
  { id: "ig-7", platform: "instagram", title: "A very long caption about the week we spent recording the mountain road at dawn and the reason the last take stayed", author: "long.form", durationSec: 90, sizeBytes: 24_000_000, ago: 12 * day, aspect: "9:16" },
  { id: "ig-8", platform: "instagram", title: "Night bus", author: "city.lights", durationSec: 21, sizeBytes: 5_400_000, ago: 21 * day, aspect: "9:16" },
  { id: "tt-1", platform: "tiktok", title: "Dance loop", author: "hoathinh", durationSec: 18, sizeBytes: 3_300_000, ago: 40 * 60 * 1000, aspect: "9:16", status: "progress", progress: 64 },
  { id: "tt-2", platform: "tiktok", title: "Recipe in 20 seconds", author: "fastcook", durationSec: 20, sizeBytes: 4_100_000, ago: 7 * hour, aspect: "9:16" },
  { id: "tt-3", platform: "tiktok", title: "Street interview", author: "ask.tj", durationSec: 44, sizeBytes: 9_600_000, ago: 30 * hour, aspect: "9:16" },
  { id: "tt-4", platform: "tiktok", title: "Before and after", author: "editlab", durationSec: 16, sizeBytes: 2_800_000, ago: 4 * day, aspect: "9:16" },
  { id: "tt-5", platform: "tiktok", title: "Cat vs cucumber, extended cut with the original sound", author: "home.zoo", durationSec: 37, sizeBytes: 6_700_000, ago: 9 * day, aspect: "9:16" },
  { id: "tt-6", platform: "tiktok", title: "Voice memo", author: "notes", durationSec: 29, sizeBytes: 5_100_000, ago: 28 * day, aspect: "9:16" },
  { id: "yt-1", platform: "youtube", title: "How the local bot sends a 1 GB file", author: "SAFI", durationSec: 754, sizeBytes: 186_000_000, ago: 3 * hour, aspect: "16:9" },
  { id: "yt-2", platform: "youtube", title: "Shorts: three cuts", author: "SAFI", durationSec: 42, sizeBytes: 11_000_000, ago: 20 * hour, aspect: "9:16" },
  { id: "yt-3", platform: "youtube", title: "Full lecture: color, type, and quiet interfaces for small screens", author: "design.school", durationSec: 4320, sizeBytes: 940_000_000, ago: 2 * day, aspect: "16:9" },
  { id: "yt-4", platform: "youtube", title: "Live replay", author: "studio.night", durationSec: 3612, sizeBytes: 1_050_000_000, ago: 5 * day, aspect: "16:9", status: "error" },
  { id: "yt-5", platform: "youtube", title: "Podcast clip", author: "gap.me", durationSec: 486, sizeBytes: 62_000_000, ago: 15 * day, aspect: "16:9" },
  { id: "yt-6", platform: "youtube", title: "Archive tape", author: "film.tj", durationSec: 1280, sizeBytes: 410_000_000, ago: 30 * day, aspect: "16:9" },
  { id: "fb-1", platform: "facebook", title: "Family dinner", author: "Safi Yalloh", durationSec: 73, sizeBytes: 22_000_000, ago: 6 * hour, aspect: "16:9" },
  { id: "fb-2", platform: "facebook", title: "Match highlights", author: "sport.page", durationSec: 196, sizeBytes: 84_000_000, ago: 27 * hour, aspect: "16:9" },
  { id: "fb-3", platform: "facebook", title: "Announcement", author: "community", durationSec: 54, sizeBytes: 14_000_000, ago: 8 * day, aspect: "9:16" },
  { id: "fb-4", platform: "facebook", title: "Workshop recording from the community hall, part two", author: "workshop", durationSec: 2400, sizeBytes: 510_000_000, ago: 18 * day, aspect: "16:9" },
];

export function buildHistory(): HistoryItem[] {
  return seeds.map((seed) => ({
    id: seed.id,
    platform: seed.platform,
    title: seed.title,
    author: seed.author,
    durationSec: seed.durationSec,
    sizeBytes: seed.sizeBytes,
    createdAt: at(seed.ago),
    sourceUrl: `https://example.com/${seed.platform}/${seed.id}`,
    status: seed.status ?? "success",
    progress: seed.progress,
    aspect: seed.aspect,
  }));
}

export const defaultProfile: Profile = {
  name: "Safi",
  username: "safi_user",
  plan: "free",
  dailyUsed: 3,
  dailyLimit: 5,
  invited: 2,
  rewardDownloads: 4,
  referralCode: "safi",
};

export const defaultSettings: Settings = {
  language: "tg",
  theme: "auto",
  defaultFormat: "video",
  defaultQuality: "720p",
  notifications: true,
};
