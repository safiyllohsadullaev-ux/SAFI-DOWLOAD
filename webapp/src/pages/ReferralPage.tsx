import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Profile } from "../api/types";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";

export function ReferralPage() {
  const { t } = useI18n();
  const { haptic } = useTelegram();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    let active = true;
    api.getProfile().then((value) => active && setProfile(value)).catch(() => active && setNote(t("common.error")));
    return () => {
      active = false;
    };
  }, [t]);

  const link = `https://t.me/SAFIi2bot?start=ref_${profile?.referralCode ?? "safi"}`;

  async function copy() {
    await navigator.clipboard.writeText(link);
    haptic("success");
    setNote(t("referral.copied"));
  }

  async function share() {
    haptic();
    if (navigator.share) {
      await navigator.share({ url: link, title: "SAFI DOWNLOADER" });
      return;
    }
    await copy();
  }

  return (
    <div className="grid gap-4">
      <h1 className="text-[22px] font-semibold">{t("referral.title")}</h1>
      <section className="rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
        <p className="text-sm text-[var(--hint)]">{t("referral.link")}</p>
        <p className="mt-2 break-all text-sm">{link}</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button type="button" className="min-h-11 rounded-xl bg-[var(--accent)] text-[var(--accent-text)]" onClick={() => void copy()}>
            {t("referral.copy")}
          </button>
          <button type="button" className="min-h-11 rounded-xl bg-[var(--bg)]" onClick={() => void share()}>
            {t("referral.share")}
          </button>
        </div>
      </section>
      <section className="grid grid-cols-2 gap-2">
        <div className="rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
          <p className="text-xs text-[var(--hint)]">{t("referral.invited")}</p>
          <p className="mt-1 text-2xl font-semibold">{profile?.invited ?? "–"}</p>
        </div>
        <div className="rounded-2xl bg-[var(--card)] p-4 shadow-[var(--shadow)]">
          <p className="text-xs text-[var(--hint)]">{t("referral.reward")}</p>
          <p className="mt-1 text-2xl font-semibold">{t("referral.rewardValue", { count: profile?.rewardDownloads ?? 0 })}</p>
        </div>
      </section>
      {note ? <p className="text-sm text-[var(--hint)]">{note}</p> : null}
    </div>
  );
}
