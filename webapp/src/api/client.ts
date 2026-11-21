import { mockApi } from "./mock";
import { realApi } from "./real";

const mockFlag = import.meta.env.VITE_USE_MOCK;
const useMock = mockFlag ? mockFlag !== "false" : !import.meta.env.VITE_API_URL;

export const api = useMock ? mockApi : realApi;
export { detectPlatform } from "./mock";
export { ApiError } from "./types";
export type * from "./types";
