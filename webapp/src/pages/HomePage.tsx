import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardPaste, Eraser } from "lucide-react";
import { api, ApiError, detectPlatform } from "../api/client";
import type { HistoryItem, MediaFormat, Preview, Profile, Quality } from "../api/types";
import { CardSkeleton } from "../components/Skeleton";
import { PlatformIcon } from "../components/PlatformIcon";
import { Segmented } from "../components/Segmented";
import { VideoCard } from "../components/VideoCard";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";
import { formatDuration } from "../lib/format";

const videoQualities: Quality[] = ["360p", "720p", "1080p"];
const audioQualities: Quality[] = ["128kbps", "320kbps"];

export function HomePage() {
  const { t } = useI18n();
  const { haptic } = useTelegram();
  const [url, setUrl] = useState("");
  const [format, setFormat] = useState<MediaFormat>("video");
  const [quality, setQuality] = useState<Quality>("720p");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [previewState, setPreviewState] = useState<"idle" | "loading" | "invalid" | "error">("idle");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [recent, setRecent] = useState<HistoryItem[]>([]);
  const [recentState, setRecentState] = useState<"loading" | "ready" | "error">("loading");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  useEffect(() => {
    let active = true;
    api.getSettings().then((settings) => {
      if (!active) return;
      setFormat(settings.defaultFormat);
      setQuality(settings.defaultQuality);
    }).catch(() => undefined);
    api.getProfile().then((value) => active && setProfile(value)).catch(() => undefined);
    api.getHistory({ platform: "all", query: "", page: 1, pageSize: 3 })
      .then((page) => {
        if (!active) return;
        setRecent(page.items);
        setRecentState("ready");
      })
      .catch(() => active && setRecentState("error"));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const platform = detectPlatform(url);
    if (!url.trim()) {
      setPreview(null);
      setPreviewState("idle");
      return;
    }
    if (!platform) {
      setPreview(null);
      setPreviewState("invalid");
      return;
    }
    setPreviewState("loading");
    const timer = window.setTimeout(() => {
      api.getPreview(url)
        .then((value) => {
          setPreview(value);
          setPreviewState("idle");
        })
        .catch((error: unknown) => {
          setPreview(null);
          setPreviewState(error instanceof ApiError && error.code === "invalid" ? "invalid" : "error");
        });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [url]);

  useEffect(() => {
    if (format === "audio" && !quality.endsWith("kbps")) setQuality("128kbps");
    if (format === "video" && quality.endsWith("kbps")) setQuality("720p");
  }, [format, quality]);

  async function paste() {
    haptic();
    try {
      setUrl(await navigator.clipboard.readText());
    } catch {
      setNote(t("home.invalid"));
    }
  }

  async function download() {
    haptic();
    setNote("");
    if (!detectPlatform(url)) {
      setPreviewState("invalid");
      return;
    }
    setBusy(true);
    try {
      const item = await api.startDownload({ url, format, quality });
      setRecent((current) => [item, ...current].slice(0, 3));
      setRecentState("ready");
      const next = await api.getProfile();
      setProfile(next);
      setUrl("");
    } catch {
      setPreviewState("error");
    } finally {
      setBusy(false);
    }
  }

  const platform = detectPlatform(url);
  const qualities = format === "audio" ? audioQualities : videoQualities;

  return (
    <div className="grid gap-4">
      <header className="flex items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-wide text-[var(--hint)]">{t("home.kicker")}</p>
          <h1 className="text-[22px] font-semibold">{t("home.title")}</h1>
        </div>
        <span className="rounded-full bg-[var(--card)] px-3 py-2 text-sm shadow-[var(--shadow)]">
          {t("home.limit", { used: profile?.dailyUsed ?? 0, limit: profile?.dailyLimit ?? 5 })}
        </span>
      </header>

      <section className="rounded-2xl bg-[var(--card)] p-3 shadow-[var(--shadow)]">
        <label htmlFor="video-url" className="mb-2 block text-sm text-[var(--hint)]">
          {t("home.link")}
        </label>
        <textarea
          id="video-url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          className="min-h-24 w-full resize-none rounded-xl bg-[var(--bg)] p-3 outline-none"
        />
        <div className="mt-2 flex gap-2">
          <button type="button" className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-[var(--bg)]" onClick={() => void paste()} aria-label={t("home.paste")}>
            <ClipboardPaste size={20} />
            {t("home.paste")}
          </button>
          <button type="button" className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-[var(--bg)]" onClick={() => { haptic(); setUrl(""); }} aria-label={t("home.clear")}>
            <Eraser size={20} />
            {t("home.clear")}
          </button>
        </div>
        {platform ? (
          <div className="mt-3 flex items-center gap-2 text-sm">
            <PlatformIcon platform={platform} label={t(`platforms.${platform}`)} />
            {t(`platforms.${platform}`)}
          </div>
        ) : null}
        {previewState === "invalid" ? <p className="mt-2 text-sm text-[var(--danger)]">{t("home.invalid")}</p> : null}
        {previewState === "error" ? <p className="mt-2 text-sm text-[var(--danger)]">{t("home.network")}</p> : null}
        {note ? <p className="mt-2 text-sm text-[var(--hint)]">{note}</p> : null}
      </section>

      {previewState === "loading" ? <CardSkeleton /> : null}
      {preview ? (
        <article className="overflow-hidden rounded-2xl bg-[var(--card)] shadow-[var(--shadow)]">
          <div
            className={preview.aspect === "9:16" ? "h-44" : "h-36"}
            style={{
              background:
                preview.platform === "youtube"
                  ? "linear-gradient(145deg,#ff4d4d,#9b0000)"
                  : "linear-gradient(145deg,#f9ce34,#ee2a7b,#6228d7)",
            }}
          />
          <div className="p-3">
            <h2 className="line-clamp-2 font-medium">{preview.title}</h2>
            <p className="mt-1 text-sm text-[var(--hint)]">
              {t("home.author")}: {preview.author} · {formatDuration(preview.durationSec)}
            </p>
          </div>
        </article>
      ) : null}

      <section className="grid gap-3 rounded-2xl bg-[var(--card)] p-3 shadow-[var(--shadow)]">
        <div>
          <p className="mb-2 text-sm text-[var(--hint)]">{t("home.format")}</p>
          <Segmented
            label={t("home.format")}
            value={format}
            onChange={setFormat}
            options={[
              { value: "video", label: t("home.video") },
              { value: "audio", label: t("home.audio") },
            ]}
          />
        </div>
        <div>
          <p className="mb-2 text-sm text-[var(--hint)]">{t("home.quality")}</p>
          <Segmented
            label={t("home.quality")}
            value={quality}
            onChange={setQuality}
            options={qualities.map((item) => ({ value: item, label: item }))}
          />
        </div>
      </section>

      <button
        type="button"
        disabled={busy}
        onClick={() => void download()}
        className="min-h-12 rounded-2xl bg-[var(--accent)] text-base font-semibold text-[var(--accent-text)] disabled:opacity-60"
      >
        {t("home.download")}
      </button>

      <section className="grid gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">{t("home.recent")}</h2>
          <Link to="/history" className="min-h-11 content-center text-sm text-[var(--accent)]">
            {t("home.seeAll")}
          </Link>
        </div>
        {recentState === "loading" ? <CardSkeleton /> : null}
        {recentState === "error" ? <p className="text-sm text-[var(--danger)]">{t("home.network")}</p> : null}
        {recentState === "ready" && recent.length === 0 ? <p className="text-sm text-[var(--hint)]">{t("home.emptyRecent")}</p> : null}
        {recent.map((item) => (
          <VideoCard key={item.id} item={item} />
        ))}
      </section>
    </div>
  );
}
