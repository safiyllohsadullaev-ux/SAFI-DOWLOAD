export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div className="h-2 overflow-hidden rounded-full bg-[var(--line)]" role="progressbar" aria-valuenow={width} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div className="h-full rounded-full bg-[var(--accent)]" style={{ width: `${width}%` }} />
    </div>
  );
}
