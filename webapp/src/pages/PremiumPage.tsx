import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { api } from "../api/client";
import { useTelegram } from "../hooks/useTelegram";
import { useI18n } from "../i18n";

const plans = [50, 150, 500];

export function PremiumPage() {
  const { t } = useI18n();
  const { haptic } = useTelegram();
  const [picked, setPicked] = useState(150);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = t("premium.title");
  }, [t]);

  const rows = [
    [t("premium.limit"), t("premium.freeLimit"), t("premium.proLimit")],
    [t("premium.quality"), t("premium.freeQuality"), t("premium.proQuality")],
    [t("premium.queue"), t("premium.freeQueue"), t("premium.proQueue")],
  ];

  async function buy() {
    setBusy(true);
    haptic();
    try {
      await api.buyPremium(picked);
      setDone(true);
      haptic("success");
    } catch {
      haptic("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4">
      <h1 className="text-[22px] font-semibold">{t("premium.title")}</h1>
      <div className="overflow-hidden rounded-2xl bg-[var(--card)] shadow-[var(--shadow)]">
        <div className="grid grid-cols-3 px-3 py-2 text-sm text-[var(--hint)]">
          <span />
          <span>{t("premium.free")}</span>
          <span>{t("premium.pro")}</span>
        </div>
        {rows.map((row) => (
          <div key={row[0]} className="grid grid-cols-3 border-t border-[var(--line)] px-3 py-3 text-sm">
            {row.map((cell) => (
              <span key={cell}>{cell}</span>
            ))}
          </div>
        ))}
      </div>
      <div className="grid gap-2">
        {plans.map((stars) => (
          <button
            key={stars}
            type="button"
            onClick={() => setPicked(stars)}
            className={`flex min-h-12 items-center justify-between rounded-2xl px-4 ${
              picked === stars ? "bg-[var(--accent)] text-[var(--accent-text)]" : "bg-[var(--card)]"
            }`}
          >
            <span className="inline-flex items-center gap-2">
              <Star size={20} />
              {t("premium.price", { stars })}
            </span>
          </button>
        ))}
      </div>
      {done ? <p className="text-sm text-[var(--ok)]">{t("premium.success")}</p> : null}
      <button type="button" disabled={busy} onClick={() => void buy()} className="min-h-12 rounded-2xl bg-[var(--accent)] font-semibold text-[var(--accent-text)] disabled:opacity-60">
        {t("premium.buy")}
      </button>
    </div>
  );
}
