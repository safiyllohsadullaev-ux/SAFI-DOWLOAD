import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Lang, MediaFormat, Quality, Settings, ThemeMode } from "../api/types";
import { ConfirmSheet } from "../components/ConfirmSheet";
import { Segmented } from "../components/Segmented";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";
import { formatSize } from "../lib/format";

const languages: Lang[] = ["tg", "ru", "en"];
const languageLabel: Record<Lang, string> = { tg: "Тоҷикӣ", ru: "Русский", en: "English" };

export function SettingsPage() {
  const { t, setLang } = useI18n();
  const { haptic } = useTelegram();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [storage, setStorage] = useState(0);
  const [confirm, setConfirm] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([api.getSettings(), api.getStats()])
      .then(([next, stats]) => {
        if (!active) return;
        setSettings(next);
        setLang(next.language);
        setStorage(stats.sizeBytes);
      })
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, [setLang]);

  async function save(patch: Partial<Settings>) {
    if (!settings) return;
    const next = { ...settings, ...patch };
    setSettings(next);
    if (patch.language) setLang(patch.language);
    haptic();
    const saved = await api.saveSettings(patch);
    setSettings(saved);
    setLang(saved.language);
  }

  if (failed) return <p className="text-sm text-[var(--danger)]">{t("common.error")}</p>;
  if (!settings) return <div className="h-40 animate-pulse rounded-2xl bg-[var(--card)]" />;

  const qualities: Quality[] = settings.defaultFormat === "audio" ? ["128kbps", "320kbps"] : ["360p", "720p", "1080p"];

  return (
    <div className="grid gap-4 xl:grid-cols-2 xl:items-start">
      <h1 className="text-[22px] font-semibold xl:col-span-2">{t("settings.title")}</h1>
      <section className="grid gap-3 rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <p className="text-sm text-[var(--hint)]">{t("settings.language")}</p>
        <Segmented
          label={t("settings.language")}
          value={settings.language}
          onChange={(language) => void save({ language })}
          options={languages.map((language) => ({ value: language, label: languageLabel[language] }))}
        />
        <p className="text-sm text-[var(--hint)]">{t("settings.theme")}</p>
        <Segmented<ThemeMode>
          label={t("settings.theme")}
          value={settings.theme}
          onChange={(theme) => void save({ theme })}
          options={[
            { value: "auto", label: t("settings.auto") },
            { value: "light", label: t("settings.light") },
            { value: "dark", label: t("settings.dark") },
          ]}
        />
        <p className="text-sm text-[var(--hint)]">{t("settings.format")}</p>
        <Segmented<MediaFormat>
          label={t("settings.format")}
          value={settings.defaultFormat}
          onChange={(defaultFormat) =>
            void save({
              defaultFormat,
              defaultQuality: defaultFormat === "audio" ? "128kbps" : "720p",
            })
          }
          options={[
            { value: "video", label: t("home.video") },
            { value: "audio", label: t("home.audio") },
          ]}
        />
        <p className="text-sm text-[var(--hint)]">{t("settings.quality")}</p>
        <Segmented
          label={t("settings.quality")}
          value={settings.defaultQuality}
          onChange={(defaultQuality) => void save({ defaultQuality })}
          options={qualities.map((quality) => ({ value: quality, label: quality }))}
        />
        <button
          type="button"
          className="flex min-h-11 items-center justify-between"
          onClick={() => void save({ notifications: !settings.notifications })}
          aria-pressed={settings.notifications}
        >
          <span>{t("settings.notifications")}</span>
          <span className="text-sm text-[var(--hint)]">{settings.notifications ? t("common.on") : t("common.off")}</span>
        </button>
      </section>
      <section className="grid gap-3 rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <div className="flex items-center justify-between">
          <span>{t("settings.storage")}</span>
          <span className="text-sm text-[var(--hint)]">{formatSize(storage)}</span>
        </div>
        <button type="button" className="min-h-11 rounded-xl bg-[var(--bg)] text-[var(--danger)]" onClick={() => setConfirm(true)}>
          {t("settings.clear")}
        </button>
      </section>
      <section className="grid gap-2 rounded-2xl bg-[var(--card)] p-4 text-sm shadow-[var(--shadow)]">
        <p>{t("settings.about")}</p>
        <p className="text-[var(--hint)]">{t("settings.version", { version: "1.0.0" })}</p>
        <a className="min-h-11 content-center text-[var(--accent)]" href="https://t.me/SAFIi2bot">
          {t("settings.support")}
        </a>
      </section>
      {confirm ? (
        <ConfirmSheet
          title={t("settings.clearTitle")}
          body={t("settings.clearBody")}
          confirmLabel={t("history.confirm")}
          cancelLabel={t("history.cancel")}
          onClose={() => setConfirm(false)}
          onConfirm={() => {
            void api.clearHistory().then(() => {
              setStorage(0);
              setConfirm(false);
              haptic("success");
            });
          }}
        />
      ) : null}
    </div>
  );
}
