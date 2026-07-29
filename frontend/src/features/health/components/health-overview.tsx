import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import type {
  HealthResponse,
  SemanticRetrievalStatus,
} from "@/features/health/types/health";

function getSemanticTone(
  status: SemanticRetrievalStatus,
):
  | "positive"
  | "warning"
  | "negative"
  | "neutral" {
  switch (status) {
    case "available":
      return "positive";

    case "cooldown":
      return "warning";

    case "unavailable":
      return "negative";

    case "disabled":
      return "neutral";
  }
}

export function HealthOverview({
  health,
}: {
  health: HealthResponse;
}) {
  return (
    <Surface>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">
              Backend service
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-950">
              {health.service}
            </h2>
          </div>

          <StatusBadge tone="positive">
            {health.status}
          </StatusBadge>
        </div>

        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <HealthItem
            label="Version"
            value={health.version}
          />

          <HealthItem
            label="Environment"
            value={health.environment}
          />

          <HealthItem
            label="Semantic retrieval"
            value={
              <StatusBadge
                tone={getSemanticTone(
                  health.semantic_retrieval_status,
                )}
              >
                {health.semantic_retrieval_status}
              </StatusBadge>
            }
          />

          <HealthItem
            label="Recovery cooldown"
            value={`${health.semantic_recovery_cooldown_seconds}s`}
          />
        </dl>

        {health.semantic_retrieval_error ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm font-medium text-amber-900">
              Semantic retrieval notice
            </p>

            <p className="mt-1 text-sm text-amber-800">
              {health.semantic_retrieval_error}
            </p>
          </div>
        ) : null}
      </div>
    </Surface>
  );
}

function HealthItem({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>

      <dd className="mt-2 text-sm font-medium text-slate-900">
        {value}
      </dd>
    </div>
  );
}