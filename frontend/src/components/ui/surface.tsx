import type { ReactNode } from "react";

export function Surface({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={[
        "rounded-2xl border border-slate-200",
        "bg-white p-6 shadow-sm",
        className,
      ].join(" ")}
    >
      {children}
    </section>
  );
}