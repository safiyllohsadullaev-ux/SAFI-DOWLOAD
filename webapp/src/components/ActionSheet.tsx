import { Copy, ExternalLink, RefreshCw, Trash2 } from "lucide-react";
import type { HistoryItem } from "../api/types";
import { useI18n } from "../i18n";

export function ActionSheet({
  item,
  onClose,
  onResend,
  onCopy,
  onOpen,
  onDelete,
}: {
  item: HistoryItem;
  onClose: () => void;
  onResend: () => void;
  onCopy: () => void;
  onOpen: () => void;
  onDelete: () => void;
}) {
  const { t } = useI18n();
  const actions = [
    { label: t("history.resend"), icon: RefreshCw, run: onResend },
    { label: t("history.copy"), icon: Copy, run: onCopy },
    { label: t("history.open"), icon: ExternalLink, run: onOpen },
    { label: t("history.delete"), icon: Trash2, run: onDelete },
  ];
  return (
    <div className="fixed inset-0 z-40 grid items-end bg-black/40 sm:items-center sm:p-6" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={t("history.actions")}
        className="mx-auto w-full max-w-md rounded-t-2xl bg-[var(--card)] p-3 pb-[max(12px,env(safe-area-inset-bottom))] sm:rounded-2xl sm:pb-3"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="line-clamp-2 px-2 pb-2 text-sm text-[var(--hint)]">{item.title}</p>
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              type="button"
              className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left"
              onClick={action.run}
            >
              <Icon size={20} />
              {action.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
