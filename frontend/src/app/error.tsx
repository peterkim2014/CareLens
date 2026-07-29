"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & {
    digest?: string;
  };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-md rounded-2xl border border-red-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium text-red-600">
          Application error
        </p>

        <h1 className="mt-2 text-2xl font-semibold text-slate-950">
          Something went wrong
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          The page could not be displayed. Try loading it
          again.
        </p>

        <button
          type="button"
          onClick={reset}
          className="mt-6 rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Try again
        </button>
      </div>
    </div>
  );
}