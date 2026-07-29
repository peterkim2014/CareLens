import type { ReactNode } from "react";

type StatusTone =
  | "positive"
  | "warning"
  | "negative"
  | "neutral";

const toneClasses: Record<StatusTone, string> = {
  positive:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
  warning:
    "border-amber-200 bg-amber-50 text-amber-700",
  negative:
    "border-red-200 bg-red-50 text-red-700",
  neutral:
    "border-slate-200 bg-slate-50 text-slate-700",
};

export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: StatusTone;
}) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full",
        "border px-2.5 py-1",
        "text-xs font-semibold capitalize",
        toneClasses[tone],
      ].join(" ")}
    >
      {children}
    </span>
  );
}