import { useEffect, useState } from "react";
import { HashRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import WebApp from "@twa-dev/sdk";
import { ChevronLeft } from "lucide-react";
import { api } from "./api/client";
import type { ThemeMode } from "./api/types";
import { BottomNav, SideNav } from "./components/BottomNav";
import { useTelegram } from "./hooks/useTelegram";
import { useTheme } from "./hooks/useTheme";
import { I18nProvider, useI18n } from "./i18n";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { PremiumPage } from "./pages/PremiumPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ReferralPage } from "./pages/ReferralPage";
import { SettingsPage } from "./pages/SettingsPage";

function Shell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setLang, t } = useI18n();
  const [theme, setTheme] = useState<ThemeMode>("auto");
  const [boot, setBoot] = useState<"loading" | "ready" | "error">("loading");
  const inner = location.pathname === "/premium" || location.pathname === "/referral";
  useTelegram();
  useTheme(theme);

  useEffect(() => {
    let active = true;
    api.getSettings()
      .then((settings) => {
        if (!active) return;
        setLang(settings.language);
        setTheme(settings.theme);
        setBoot("ready");
      })
      .catch(() => active && setBoot("error"));
    return () => {
      active = false;
    };
  }, [setLang]);

  useEffect(() => {
    const onClick = () => navigate(-1);
    if (!inner) {
      WebApp.BackButton.hide();
      return;
    }
    WebApp.BackButton.show();
    WebApp.BackButton.onClick(onClick);
    return () => {
      WebApp.BackButton.offClick(onClick);
      WebApp.BackButton.hide();
    };
  }, [inner, navigate]);

  return (
    <div className="flex min-h-dvh w-full bg-[var(--bg)]">
      {boot === "ready" ? <SideNav /> : null}
      <div className="flex min-h-dvh min-w-0 flex-1 flex-col">
        <main className={`mx-auto w-full max-w-6xl flex-1 px-4 pt-[max(12px,env(safe-area-inset-top))] sm:px-6 lg:max-w-none lg:px-8 xl:px-10 ${inner ? "pb-8" : "pb-28 lg:pb-8"}`}>
          {boot === "loading" ? <div className="h-48 animate-pulse rounded-2xl bg-[var(--card)]" /> : null}
          {boot === "error" ? (
            <div className="mx-auto grid w-full max-w-md gap-3 rounded-2xl bg-[var(--card)] p-4 text-center">
              <p>{t("common.error")}</p>
              <button type="button" className="min-h-11 rounded-xl bg-[var(--accent)] text-[var(--accent-text)]" onClick={() => window.location.reload()}>
                {t("common.retry")}
              </button>
            </div>
          ) : null}
          {boot === "ready" && inner ? (
            <button type="button" className="mb-3 inline-flex min-h-11 items-center gap-1 text-sm" onClick={() => navigate("/profile")}>
              <ChevronLeft size={20} />
              {t("common.back")}
            </button>
          ) : null}
          {boot === "ready" ? (
            <Routes>
              <Route index element={<HomePage />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="premium" element={<PremiumPage />} />
              <Route path="referral" element={<ReferralPage />} />
            </Routes>
          ) : null}
        </main>
      </div>
      {boot === "ready" && !inner ? <BottomNav /> : null}
    </div>
  );
}

export function App() {
  return (
    <I18nProvider>
      <HashRouter>
        <Shell />
      </HashRouter>
    </I18nProvider>
  );
}
