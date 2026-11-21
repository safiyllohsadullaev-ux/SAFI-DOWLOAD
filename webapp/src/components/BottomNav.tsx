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
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-[var(--line)] bg-[var(--card)] pb-[env(safe-area-inset-bottom)]">
      <ul className="mx-auto grid w-full max-w-6xl grid-cols-4">
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
                  `flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${
                    isActive ? "text-[var(--accent)]" : "text-[var(--hint)]"
                  }`
                }
              >
                <Icon size={22} strokeWidth={2} />
                {label}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
