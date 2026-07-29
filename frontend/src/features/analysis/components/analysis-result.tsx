import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import type {
  AnalysisResult,
  RiskLevel,
} from "@/features/analysis/types/analysis";

type StatusTone =
  | "positive"
  | "warning"
  | "negative"
  | "neutral";

function getRiskTone(
  riskLevel: RiskLevel,
): StatusTone {
  switch (riskLevel) {
    case "low":
      return "positive";

    case "moderate":
      return "warning";

    case "high":
    case "emergency":
      return "negative";
  }
}

export function AnalysisResultView({
  result,
}: {
  result: AnalysisResult;
}) {
  return (
    <Surface>
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">
              Analysis result
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-950">
              Clinical guidance
            </h2>
          </div>

          <StatusBadge
            tone={getRiskTone(
              result.risk_assessment.risk_level,
            )}
          >
            {result.risk_assessment.risk_level}
          </StatusBadge>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-950">
            Risk rationale
          </h3>

          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {result.risk_assessment.rationale}
          </p>
        </div>

        <div className="border-t border-slate-200 pt-6">
          <h3 className="text-sm font-semibold text-slate-950">
            Response
          </h3>

          <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {result.response}
          </p>
        </div>

        {result.trace_id ? (
          <div className="border-t border-slate-200 pt-4">
            <p className="font-mono text-xs text-slate-500">
              Trace ID: {result.trace_id}
            </p>
          </div>
        ) : null}
      </div>
    </Surface>
  );
}