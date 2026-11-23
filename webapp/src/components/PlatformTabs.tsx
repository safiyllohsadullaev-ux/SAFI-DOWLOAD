import type { Platform } from "../api/types";
import { useI18n } from "../i18n";
import { PlatformIcon } from "./PlatformIcon";

const tabs: Array<Platform | "all"> = ["all", "instagram", "tiktok", "youtube", "facebook"];

export function PlatformTabs({
  value,
  counts,
  onChange,
}: {
  value: Platform | "all";
  counts: Record<Platform | "all", number>;
  onChange: (value: Platform | "all") => void;
}) {
  const { t } = useI18n();
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 lg:flex-wrap lg:overflow-visible" role="tablist">
      {tabs.map((tab) => {
        const active = tab === value;
        const label = tab === "all" ? t("history.all") : t(`platforms.${tab}`);
        return (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab)}
            className={`inline-flex min-h-11 shrink-0 items-center gap-2 rounded-full px-3 text-sm ${
              active ? "bg-[var(--accent)] text-[var(--accent-text)]" : "bg-[var(--card)] text-[var(--text)]"
            }`}
          >
            {tab !== "all" ? <PlatformIcon platform={tab} label={label} size={16} /> : null}
            <span>{label}</span>
            <span className={`rounded-full px-1.5 text-xs ${active ? "bg-white/20" : "bg-[var(--bg)] text-[var(--hint)]"}`}>
              {counts[tab]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
