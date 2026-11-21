export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-[var(--line)] ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="flex gap-3 rounded-2xl bg-[var(--card)] p-3 shadow-[var(--shadow)]">
      <Skeleton className="h-24 w-28" />
      <div className="flex flex-1 flex-col gap-2 py-1">
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-4 w-3/5" />
        <Skeleton className="mt-auto h-3 w-1/2" />
      </div>
    </div>
  );
}
