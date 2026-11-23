export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(option.value)}
            className={`min-h-11 min-w-0 flex-1 rounded-xl px-2 text-center text-sm leading-tight sm:px-3 ${
              active ? "bg-[var(--accent)] text-[var(--accent-text)]" : "bg-[var(--bg)]"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
