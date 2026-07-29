import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="text-center">
        <p className="text-sm font-semibold text-slate-500">
          404
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-slate-950">
          Page not found
        </h1>

        <Link
          href="/"
          className="mt-6 inline-flex rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white"
        >
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}