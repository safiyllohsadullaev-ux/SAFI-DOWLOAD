/// <reference types="vite/client" />

interface TelegramHaptic {
  impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
  notificationOccurred: (type: "error" | "success" | "warning") => void;
  selectionChanged: () => void;
}

interface TelegramBackButton {
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
}

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_premium?: boolean;
}

interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  close: () => void;
  initData: string;
  initDataUnsafe: { user?: TelegramUser };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string | undefined>;
  HapticFeedback: TelegramHaptic;
  BackButton: TelegramBackButton;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  onEvent: (event: string, cb: () => void) => void;
  offEvent: (event: string, cb: () => void) => void;
}

interface TelegramNamespace {
  WebApp: TelegramWebApp;
}

declare global {
  interface ImportMetaEnv {
    readonly VITE_USE_MOCK: string;
    readonly VITE_API_URL: string;
  }

  interface Window {
    Telegram?: TelegramNamespace;
  }
}

export {};
