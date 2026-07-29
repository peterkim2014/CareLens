"use client";

import { useFormStatus } from "react-dom";

export function AnalysisSubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className={[
        "inline-flex min-h-11 items-center justify-center",
        "rounded-lg bg-slate-950 px-5",
        "text-sm font-semibold text-white",
        "transition-colors",
        "hover:bg-slate-800",
        "disabled:cursor-not-allowed",
        "disabled:bg-slate-400",
      ].join(" ")}
    >
      {pending
        ? "Analyzing…"
        : "Analyze clinical query"}
    </button>
  );
}