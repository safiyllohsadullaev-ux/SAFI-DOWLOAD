import { useEffect } from "react";
import WebApp from "@twa-dev/sdk";

export function useTelegram() {
  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    const params = WebApp.themeParams;
    const root = document.documentElement;
    const map: Record<string, string | undefined> = {
      "--tg-theme-bg-color": params.bg_color,
      "--tg-theme-text-color": params.text_color,
      "--tg-theme-hint-color": params.hint_color,
      "--tg-theme-button-color": params.button_color,
      "--tg-theme-button-text-color": params.button_text_color,
      "--tg-theme-secondary-bg-color": params.secondary_bg_color,
    };
    for (const [key, value] of Object.entries(map)) {
      if (value) root.style.setProperty(key, value);
    }
  }, []);

  const user = WebApp.initDataUnsafe.user;

  return {
    user,
    colorScheme: WebApp.colorScheme,
    haptic(kind: "light" | "success" | "error" = "light") {
      if (kind === "light") WebApp.HapticFeedback.impactOccurred("light");
      else WebApp.HapticFeedback.notificationOccurred(kind);
    },
  };
}
