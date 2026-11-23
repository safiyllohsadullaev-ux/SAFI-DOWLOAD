export function ConfirmSheet({
  title,
  body,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onClose,
}: {
  title: string;
  body: string;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-40 grid items-end bg-black/40 sm:items-center sm:p-6" role="presentation" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="mx-auto w-full max-w-md rounded-t-2xl bg-[var(--card)] p-4 pb-[max(16px,env(safe-area-inset-bottom))] sm:rounded-2xl sm:pb-4"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-[var(--hint)]">{body}</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button type="button" className="min-h-11 rounded-xl bg-[var(--bg)]" onClick={onClose}>
            {cancelLabel}
          </button>
          <button type="button" className="min-h-11 rounded-xl bg-[var(--danger)] text-white" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
