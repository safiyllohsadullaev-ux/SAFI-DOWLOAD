import { Camera, Clapperboard, Music2, Users } from "lucide-react";
import type { Platform } from "../api/types";

const icons = {
  instagram: Camera,
  tiktok: Music2,
  youtube: Clapperboard,
  facebook: Users,
} as const;

const styles: Record<Platform, string> = {
  instagram: "bg-[linear-gradient(135deg,var(--ig-a),var(--ig-b),var(--ig-c))] text-white",
  tiktok: "bg-[linear-gradient(135deg,var(--tt),#222_55%,var(--tt-b))] text-white",
  youtube: "bg-[var(--yt)] text-white",
  facebook: "bg-[var(--fb)] text-white",
};

export function PlatformIcon({
  platform,
  label,
  size = 20,
}: {
  platform: Platform;
  label: string;
  size?: number;
}) {
  const Icon = icons[platform];
  return (
    <span
      className={`inline-grid h-7 w-7 shrink-0 place-items-center rounded-lg ${styles[platform]}`}
      aria-hidden="true"
      title={label}
    >
      <Icon size={size} strokeWidth={2} />
    </span>
  );
}
