import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Platform, Profile, Stats } from "../api/types";
import { ProgressBar } from "../components/ProgressBar";
import { CardSkeleton } from "../components/Skeleton";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";
import { formatSize } from "../lib/format";

const order: Platform[] = ["instagram", "tiktok", "youtube", "facebook"];
const colors: Record<Platform, string> = {
  instagram: "linear-gradient(90deg, var(--ig-a), var(--ig-b), var(--ig-c))",
  tiktok: "linear-gradient(90deg, var(--tt), var(--tt-b))",
  youtube: "var(--yt)",
  facebook: "var(--fb)",
};

export function ProfilePage() {
  const { t } = useI18n();
  const { user, haptic } = useTelegram();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([api.getProfile(), api.getStats()])
      .then(([nextProfile, nextStats]) => {
        if (!active) return;
        setProfile(nextProfile);
        setStats(nextStats);
      })
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, []);

  if (failed) return <p className="text-sm text-[var(--danger)]">{t("common.error")}</p>;
  if (!profile || !stats) {
    return (
      <div className="grid gap-3">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(" ") : profile.name;
  const username = user?.username || profile.username;
  const initial = name.slice(0, 1).toUpperCase();
  const limit = profile.dailyLimit || 1;

  return (
    <div className="grid gap-4">
      <section className="flex items-center gap-3 rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <div className="grid h-16 w-16 place-items-center overflow-hidden rounded-2xl bg-[var(--accent)] text-xl font-semibold text-[var(--accent-text)]">
          {user?.photo_url ? <img src={user.photo_url} alt="" className="h-full w-full object-cover" /> : initial}
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold">{name}</h1>
          <p className="truncate text-sm text-[var(--hint)]">@{username}</p>
          <span className="mt-1 inline-flex rounded-full bg-[var(--bg)] px-2 py-1 text-xs">
            {profile.plan === "premium" ? t("profile.premium") : t("profile.free")}
          </span>
        </div>
      </section>

      <section className="grid grid-cols-3 gap-2">
        {[
          [t("profile.total"), String(stats.total)],
          [t("profile.week"), String(stats.week)],
          [t("profile.size"), formatSize(stats.sizeBytes)],
        ].map(([label, value]) => (
          <div key={label} className="min-w-0 rounded-2xl bg-[var(--card)] p-3 shadow-[var(--shadow)]">
            <p className="text-xs text-[var(--hint)]">{label}</p>
            <p className="mt-1 truncate font-semibold">{value}</p>
          </div>
        ))}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <div className="mb-2 flex justify-between gap-3 text-sm">
          <span>{t("profile.limit")}</span>
          <span>
            {profile.dailyUsed}/{profile.dailyLimit}
          </span>
        </div>
        <ProgressBar value={(profile.dailyUsed / limit) * 100} label={t("profile.limit")} />
      </section>

      <section className="grid gap-3 rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <h2 className="text-sm text-[var(--hint)]">{t("profile.chart")}</h2>
        {order.map((platform) => {
          const count = stats.byPlatform[platform];
          const share = stats.total ? Math.round((count / stats.total) * 100) : 0;
          return (
            <div key={platform}>
              <div className="mb-1 flex justify-between text-sm">
                <span>{t(`platforms.${platform}`)}</span>
                <span className="text-[var(--hint)]">{share}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[var(--line)]">
                <div className="h-full rounded-full" style={{ width: `${share}%`, background: colors[platform] }} />
              </div>
            </div>
          );
        })}
      </section>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
      <button type="button" className="min-h-12 rounded-2xl bg-[var(--accent)] font-semibold text-[var(--accent-text)]" onClick={() => { haptic(); navigate("/premium"); }}>
        {t("profile.getPremium")}
      </button>
      <button type="button" className="min-h-12 rounded-2xl bg-[var(--card)] shadow-[var(--shadow)]" onClick={() => { haptic(); navigate("/referral"); }}>
        {t("profile.invite")}
      </button>
      </div>
    </div>
  );
}
