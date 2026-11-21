import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import en from "./en.json";
import ru from "./ru.json";
import tg from "./tg.json";
import type { Lang } from "../api/types";

const dictionaries = { tg, ru, en };

type Vars = Record<string, string | number>;

function lookup(lang: Lang, key: string): string {
  const parts = key.split(".");
  let node: unknown = dictionaries[lang];
  for (const part of parts) {
    if (typeof node !== "object" || node === null || !(part in node)) return key;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === "string" ? node : key;
}

export function translate(lang: Lang, key: string, vars?: Vars): string {
  return lookup(lang, key).replace(/\{(\w+)\}/g, (_, name: string) => String(vars?.[name] ?? ""));
}

interface I18nValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Vars) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("tg");
  const value = useMemo<I18nValue>(
    () => ({ lang, setLang, t: (key, vars) => translate(lang, key, vars) }),
    [lang],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error("i18n");
  return value;
}
