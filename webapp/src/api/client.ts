import { mockApi } from "./mock";
import { realApi } from "./real";

const mockFlag = import.meta.env.VITE_USE_MOCK;
const realConfigured = mockFlag === "false" || Boolean(import.meta.env.VITE_API_URL);
const insideTelegram = Boolean(window.Telegram?.WebApp?.initData);
const useMock = mockFlag === "true" || !realConfigured || !insideTelegram;

export const api = useMock ? mockApi : realApi;
export { detectPlatform } from "./mock";
export { ApiError } from "./types";
export type * from "./types";
