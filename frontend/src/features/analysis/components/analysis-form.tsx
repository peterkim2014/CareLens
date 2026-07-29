"use client";

import { useActionState } from "react";

import { Surface } from "@/components/ui/surface";
import { submitAnalysis } from "@/features/analysis/actions/submit-analysis";
import { initialAnalysisFormState } from "@/features/analysis/types/analysis";

import { AnalysisResultView } from "./analysis-result";
import { AnalysisSubmitButton } from "./analysis-submit-button";

const MAXIMUM_QUERY_LENGTH = 4_000;

export function AnalysisForm() {
  const [state, formAction] = useActionState(
    submitAnalysis,
    initialAnalysisFormState,
  );

  const queryErrors = state.errors.query ?? [];

  return (
    <div className="space-y-8">
      <Surface>
        <form
          action={formAction}
          className="space-y-6"
        >
          <div>
            <p className="text-sm font-medium text-slate-500">
              Clinical analysis
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-950">
              Submit a clinical scenario
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Provide the relevant symptoms, context,
              timeline, and clinical question.
            </p>
          </div>

          <div>
            <label
              htmlFor="query"
              className="block text-sm font-semibold text-slate-900"
            >
              Clinical query
            </label>

            <textarea
              id="query"
              name="query"
              rows={10}
              maxLength={MAXIMUM_QUERY_LENGTH}
              defaultValue={state.values.query}
              aria-invalid={queryErrors.length > 0}
              aria-describedby={
                queryErrors.length > 0
                  ? "query-errors"
                  : "query-description"
              }
              placeholder="Example: A patient presents with..."
              className={[
                "mt-2 block w-full resize-y rounded-xl",
                "border bg-white px-4 py-3",
                "text-sm leading-6 text-slate-950",
                "outline-none transition",
                "placeholder:text-slate-400",
                queryErrors.length > 0
                  ? "border-red-300 focus:border-red-500 focus:ring-4 focus:ring-red-100"
                  : "border-slate-300 focus:border-slate-500 focus:ring-4 focus:ring-slate-100",
              ].join(" ")}
            />

            {queryErrors.length > 0 ? (
              <div
                id="query-errors"
                className="mt-2 space-y-1"
              >
                {queryErrors.map((error) => (
                  <p
                    key={error}
                    className="text-sm text-red-700"
                  >
                    {error}
                  </p>
                ))}
              </div>
            ) : (
              <p
                id="query-description"
                className="mt-2 text-xs text-slate-500"
              >
                Do not include directly identifying
                patient information.
              </p>
            )}
          </div>

          {state.status === "validation_error" ? (
            <div
              role="alert"
              className="rounded-xl border border-amber-200 bg-amber-50 p-4"
            >
              <p className="text-sm font-semibold text-amber-900">
                Review the form
              </p>

              <p className="mt-1 text-sm leading-6 text-amber-800">
                {state.message}
              </p>
            </div>
          ) : null}

          {state.status === "error" ? (
            <div
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 p-4"
            >
              <p className="text-sm font-semibold text-red-900">
                Analysis failed
              </p>

              <p className="mt-1 text-sm leading-6 text-red-800">
                {state.message}
              </p>

              {state.traceId ? (
                <p className="mt-3 font-mono text-xs text-red-700">
                  Trace ID: {state.traceId}
                </p>
              ) : null}
            </div>
          ) : null}

          <div className="flex items-center justify-between gap-4 border-t border-slate-200 pt-6">
            <p className="text-xs text-slate-500">
              Maximum{" "}
              {MAXIMUM_QUERY_LENGTH.toLocaleString()}
              {" "}characters
            </p>

            <AnalysisSubmitButton />
          </div>
        </form>
      </Surface>

      {state.status === "success" ? (
        <AnalysisResultView
          result={state.result}
        />
      ) : null}
    </div>
  );
}