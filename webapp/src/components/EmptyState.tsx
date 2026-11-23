import { Inbox } from "lucide-react";

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="grid w-full place-items-center rounded-2xl bg-[var(--card)] px-6 py-14 text-center shadow-[var(--shadow)]">
      <Inbox size={36} className="text-[var(--hint)]" />
      <p className="mt-3 max-w-56 text-sm text-[var(--hint)]">{text}</p>
    </div>
  );
}
