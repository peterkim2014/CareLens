import { AppShell } from "@/components/layout/app-shell";
import { AnalysisForm } from "@/features/analysis/components/analysis-form";
import { getHealth } from "@/features/health/api/get-health";
import { HealthOverview } from "@/features/health/components/health-overview";
import type { HealthResponse } from "@/features/health/types/health";
import { APIError } from "@/lib/api/api-error";

type HealthState =
  | {
      status: "success";
      health: HealthResponse;
    }
  | {
      status: "error";
      message: string;
      traceId?: string;
    };

async function loadHealth(): Promise<HealthState> {
  try {
    const health = await getHealth();

    return {
      status: "success",
      health,
    };
  } catch (error) {
    if (error instanceof APIError) {
      return {
        status: "error",
        message: error.message,
        traceId: error.traceId,
      };
    }

    return {
      status: "error",
      message:
        "The backend health status could not be loaded.",
    };
  }
}

export default async function Home() {
  const healthState = await loadHealth();

  return (
    <AppShell>
      <div className="space-y-10">
        <header>
          <p className="text-sm font-medium text-slate-500">
            Clinical workspace
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
            CareLens dashboard
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            Review backend availability and submit
            clinical scenarios for grounded analysis.
          </p>
        </header>

        {healthState.status === "success" ? (
          <HealthOverview
            health={healthState.health}
          />
        ) : (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-6">
            <p className="font-semibold text-red-900">
              Backend unavailable
            </p>

            <p className="mt-2 text-sm leading-6 text-red-800">
              {healthState.message}
            </p>

            {healthState.traceId ? (
              <p className="mt-4 font-mono text-xs text-red-700">
                Trace ID: {healthState.traceId}
              </p>
            ) : null}
          </section>
        )}

        <AnalysisForm />
      </div>
    </AppShell>
  );
}