import type { HistoryItem } from "../api/types";

export function formatDuration(total: number): string {
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const pad = (value: number) => String(value).padStart(2, "0");
  if (hours > 0) return `${hours}:${pad(minutes)}:${pad(seconds)}`;
  return `${minutes}:${pad(seconds)}`;
}

export function formatSize(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${Math.round(bytes / 1024 ** 2)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export type DateGroup = "today" | "yesterday" | "week" | "earlier";

export function dateGroup(iso: string): DateGroup {
  const date = new Date(iso);
  const now = new Date();
  const start = (value: Date) => new Date(value.getFullYear(), value.getMonth(), value.getDate()).getTime();
  const day = 24 * 60 * 60 * 1000;
  const diff = start(now) - start(date);
  if (diff <= 0) return "today";
  if (diff <= day) return "yesterday";
  if (diff <= 6 * day) return "week";
  return "earlier";
}

export function relativeTime(
  iso: string,
  t: (key: string, vars?: Record<string, string | number>) => string,
): string {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return t("time.now");
  if (minutes < 60) return t("time.minutes", { count: minutes });
  const hours = Math.round(minutes / 60);
  if (hours < 24) return t("time.hours", { count: hours });
  return t("time.days", { count: Math.round(hours / 24) });
}

export function groupItems(items: HistoryItem[]): Array<{ key: DateGroup; items: HistoryItem[] }> {
  const order: DateGroup[] = ["today", "yesterday", "week", "earlier"];
  return order
    .map((key) => ({ key, items: items.filter((item) => dateGroup(item.createdAt) === key) }))
    .filter((group) => group.items.length > 0);
}
