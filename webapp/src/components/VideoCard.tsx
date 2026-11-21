import { MoreVertical } from "lucide-react";
import type { HistoryItem } from "../api/types";
import { useI18n } from "../i18n";
import { formatDuration, formatSize, relativeTime } from "../lib/format";
import { PlatformIcon } from "./PlatformIcon";
import { ProgressBar } from "./ProgressBar";

const wash: Record<HistoryItem["platform"], string> = {
  instagram: "linear-gradient(145deg, #f9ce34, #ee2a7b 55%, #6228d7)",
  tiktok: "linear-gradient(145deg, #111, #222 40%, #25f4ee)",
  youtube: "linear-gradient(145deg, #ff4d4d, #9b0000)",
  facebook: "linear-gradient(145deg, #4c9aff, #1877f2)",
};

export function VideoCard({ item, onOpen }: { item: HistoryItem; onOpen?: (item: HistoryItem) => void }) {
  const { t } = useI18n();
  const platformLabel = t(`platforms.${item.platform}`);
  const frame = item.aspect === "9:16" ? "h-24 w-[54px]" : "h-24 w-36";
  return (
    <article className="flex gap-3 rounded-2xl bg-[var(--card)] p-3 shadow-[var(--shadow)]">
      <div className={`${frame} shrink-0 rounded-xl`} style={{ background: wash[item.platform] }} />
      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-2">
          <h3 className="line-clamp-2 flex-1 text-[15px] font-medium leading-5">{item.title}</h3>
          {onOpen ? (
            <button
              type="button"
              className="grid h-11 w-11 shrink-0 place-items-center rounded-xl"
              aria-label={t("history.actions")}
              onClick={() => onOpen(item)}
            >
              <MoreVertical size={20} />
            </button>
          ) : null}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--hint)]">
          <PlatformIcon platform={item.platform} label={platformLabel} size={14} />
          <span>{formatDuration(item.durationSec)}</span>
          <span>{formatSize(item.sizeBytes)}</span>
          <span>{relativeTime(item.createdAt, t)}</span>
          {item.status === "error" ? <span className="text-[var(--danger)]">{t("history.failed")}</span> : null}
        </div>
        {item.status === "progress" ? (
          <div className="mt-2">
            <ProgressBar value={item.progress ?? 0} label={`${item.progress ?? 0}%`} />
          </div>
        ) : null}
      </div>
    </article>
  );
}
