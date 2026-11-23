import { Download, History, Settings, User } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useI18n } from "../i18n";

const items = [
  { to: "/", icon: Download, key: "nav.home", end: true },
  { to: "/history", icon: History, key: "nav.history", end: false },
  { to: "/profile", icon: User, key: "nav.profile", end: false },
  { to: "/settings", icon: Settings, key: "nav.settings", end: false },
] as const;

export function BottomNav() {
  const { t } = useI18n();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-[var(--line)] bg-[var(--card)] pb-[env(safe-area-inset-bottom)] lg:hidden">
      <ul className="mx-auto grid w-full max-w-lg grid-cols-4">
        {items.map((item) => {
          const Icon = item.icon;
          const label = t(item.key);
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                aria-label={label}
                className={({ isActive }) =>
                  `flex min-h-14 flex-col items-center justify-center gap-1 px-1 text-center text-[11px] leading-tight sm:text-xs ${
                    isActive ? "text-[var(--accent)]" : "text-[var(--hint)]"
                  }`
                }
              >
                <Icon size={22} strokeWidth={2} />
                <span className="max-w-full truncate">{label}</span>
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function SideNav() {
  const { t } = useI18n();
  return (
    <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r border-[var(--line)] bg-[var(--card)] px-3 py-5 lg:flex xl:w-64">
      <div className="px-3 pb-6">
        <p className="text-xs tracking-wide text-[var(--hint)]">SAFI</p>
        <p className="text-lg font-semibold leading-tight">DOWNLOADER</p>
      </div>
      <ul className="grid gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const label = t(item.key);
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm ${
                    isActive ? "bg-[var(--accent)] text-[var(--accent-text)]" : "text-[var(--text)] hover:bg-[var(--bg)]"
                  }`
                }
              >
                <Icon size={20} strokeWidth={2} />
                {label}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
