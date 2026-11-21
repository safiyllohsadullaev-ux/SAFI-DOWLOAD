import { useEffect } from "react";
import WebApp from "@twa-dev/sdk";
import type { ThemeMode } from "../api/types";
import { useTelegram } from "./useTelegram";

export function useTheme(mode: ThemeMode) {
  const { colorScheme } = useTelegram();

  useEffect(() => {
    const root = document.documentElement;
    const resolved = mode === "auto" ? colorScheme : mode;
    if (mode === "auto") root.removeAttribute("data-theme");
    else root.dataset.theme = mode;
    const color = resolved === "dark" ? "#0e1621" : "#f4f7fb";
    try {
      WebApp.setHeaderColor(color);
      WebApp.setBackgroundColor(color);
    } catch {
      /* Outside Telegram the color setters can reject. */
    }
  }, [mode, colorScheme]);
}
