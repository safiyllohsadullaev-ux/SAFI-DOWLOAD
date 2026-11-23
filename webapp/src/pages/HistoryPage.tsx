import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api } from "../api/client";
import type { HistoryItem, Platform } from "../api/types";
import { ActionSheet } from "../components/ActionSheet";
import { ConfirmSheet } from "../components/ConfirmSheet";
import { EmptyState } from "../components/EmptyState";
import { PlatformTabs } from "../components/PlatformTabs";
import { CardSkeleton } from "../components/Skeleton";
import { VideoCard } from "../components/VideoCard";
import { useHistory } from "../hooks/useHistory";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";
import { groupItems } from "../lib/format";

export function HistoryPage() {
  const { t } = useI18n();
  const { haptic } = useTelegram();
  const [tab, setTab] = useState<Platform | "all">("all");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  const history = useHistory(tab, search);
  const [active, setActive] = useState<HistoryItem | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [toast, setToast] = useState("");

  function flash(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 1600);
  }

  async function copy(item: HistoryItem) {
    await navigator.clipboard.writeText(item.sourceUrl);
    haptic("success");
    flash(t("history.copied"));
    setActive(null);
  }

  async function resend(item: HistoryItem) {
    await api.resendItem(item.id);
    haptic("success");
    flash(t("history.resent"));
    setActive(null);
  }

  async function remove(item: HistoryItem) {
    await api.deleteItem(item.id);
    history.remove(item.id);
    haptic("success");
    setConfirm(false);
    setActive(null);
  }

  const groups = groupItems(history.items);

  return (
    <div className="grid gap-3">
      <h1 className="text-[22px] font-semibold">{t("history.title")}</h1>
      <label className="flex min-h-11 items-center gap-2 rounded-2xl bg-[var(--card)] px-3 shadow-[var(--shadow)]">
        <Search size={20} className="text-[var(--hint)]" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("history.search")}
          aria-label={t("history.search")}
          className="h-11 w-full bg-transparent outline-none"
        />
      </label>
      <PlatformTabs
        value={tab}
        counts={history.counts}
        onChange={(next) => {
          haptic();
          setTab(next);
        }}
      />
      {history.status === "loading" && history.items.length === 0 ? (
        <div className="grid gap-3">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : null}
      {history.status === "error" ? (
        <div className="grid gap-3 rounded-2xl bg-[var(--card)] p-4 text-center">
          <p className="text-sm text-[var(--danger)]">{t("common.error")}</p>
          <button type="button" className="min-h-11 rounded-xl bg-[var(--accent)] text-[var(--accent-text)]" onClick={() => void history.reload()}>
            {t("common.retry")}
          </button>
        </div>
      ) : null}
      {history.status === "ready" && history.items.length === 0 ? <EmptyState text={t("history.empty")} /> : null}
      {groups.map((group) => (
        <section key={group.key} className="grid gap-2">
          <h2 className="text-sm text-[var(--hint)]">{t(`history.${group.key}`)}</h2>
          <div className="grid gap-2 md:grid-cols-2">
            {group.items.map((item) => (
              <VideoCard key={item.id} item={item} onOpen={setActive} />
            ))}
          </div>
        </section>
      ))}
      {history.hasMore ? (
        <button type="button" className="min-h-11 rounded-xl bg-[var(--card)]" onClick={() => void history.loadMore()}>
          {t("history.more")}
        </button>
      ) : null}
      {toast ? <p className="fixed bottom-24 left-1/2 z-30 -translate-x-1/2 rounded-full bg-[var(--text)] px-4 py-2 text-sm text-[var(--bg)]">{toast}</p> : null}
      {active && !confirm ? (
        <ActionSheet
          item={active}
          onClose={() => setActive(null)}
          onResend={() => void resend(active)}
          onCopy={() => void copy(active)}
          onOpen={() => {
            window.open(active.sourceUrl, "_blank", "noopener,noreferrer");
            setActive(null);
          }}
          onDelete={() => setConfirm(true)}
        />
      ) : null}
      {active && confirm ? (
        <ConfirmSheet
          title={t("history.deleteTitle")}
          body={t("history.deleteBody")}
          confirmLabel={t("history.confirm")}
          cancelLabel={t("history.cancel")}
          onClose={() => setConfirm(false)}
          onConfirm={() => void remove(active)}
        />
      ) : null}
    </div>
  );
}
