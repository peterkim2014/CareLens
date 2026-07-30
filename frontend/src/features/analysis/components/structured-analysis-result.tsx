import type {
    StructuredAnalysisResult,
  } from "@/features/analysis/types/analysis";
  
  function Section({
    title,
    children,
  }: {
    title: string;
    children: React.ReactNode;
  }) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-950">
          {title}
        </h3>
  
        <div className="mt-4">
          {children}
        </div>
      </section>
    );
  }
  
  function EmptyMessage() {
    return (
      <p className="text-sm text-slate-500">
        No information was returned for this section.
      </p>
    );
  }
  
  export function StructuredAnalysisResultView({
    result,
  }: {
    result: StructuredAnalysisResult;
  }) {
    const diagnosis =
  result.most_likely_diagnosis;

    const confidence =
    diagnosis?.confidence ?? null;
  
    return (
      <div className="space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white">
          <p className="text-sm font-medium text-slate-300">
            Most likely diagnosis
          </p>
  
          <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
            <h2 className="text-2xl font-semibold">
                {diagnosis?.name ?? "Analysis unavailable"}
            </h2>
  
            {confidence !== null ? (
              <p className="text-sm font-semibold text-slate-200">
                {Math.round(confidence * 100)}% confidence
              </p>
            ) : null}
          </div>
  
          {diagnosis?.reasoning?.length > 0 ? (
            <ul className="mt-5 space-y-2 text-sm leading-6 text-slate-200">
              {diagnosis.reasoning.map((item) => (
                  <li
                    key={item}
                    className="flex gap-3"
                  >
                    <span aria-hidden="true">
                      •
                    </span>
                    <span>{item}</span>
                  </li>
                ),
              )}
            </ul>
          ) : null}
        </div>
  
        <div className="grid gap-6 lg:grid-cols-2">
          <Section title="Supporting evidence">
            {result.supporting_evidence.length > 0 ? (
              <ul className="space-y-3">
                {result.supporting_evidence.map(
                  (item) => (
                    <li
                      key={item}
                      className="flex gap-3 text-sm leading-6 text-slate-700"
                    >
                      <span
                        aria-hidden="true"
                        className="font-semibold text-emerald-700"
                      >
                        ✓
                      </span>
                      <span>{item}</span>
                    </li>
                  ),
                )}
              </ul>
            ) : (
              <EmptyMessage />
            )}
          </Section>
  
          <Section title="Differential diagnoses">
            {result.differential_diagnoses.length > 0 ? (
              <div className="space-y-4">
                {result.differential_diagnoses.map(
                  (diagnosis) => (
                    <article
                      key={diagnosis.name}
                      className="border-b border-slate-100 pb-4 last:border-0 last:pb-0"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h4 className="text-sm font-semibold text-slate-950">
                          {diagnosis.name}
                        </h4>
  
                        {diagnosis.urgency ? (
                          <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-900">
                            {diagnosis.urgency}
                          </span>
                        ) : null}
                      </div>
  
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {diagnosis.reasoning}
                      </p>
                    </article>
                  ),
                )}
              </div>
            ) : (
              <EmptyMessage />
            )}
          </Section>
  
          <Section title="Recommended tests">
            {result.recommended_tests.length > 0 ? (
              <div className="space-y-4">
                {result.recommended_tests.map(
                  (test) => (
                    <article key={test.name}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h4 className="text-sm font-semibold text-slate-950">
                          {test.name}
                        </h4>
  
                        {test.priority ? (
                          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                            {test.priority}
                          </span>
                        ) : null}
                      </div>
  
                      <p className="mt-1 text-sm leading-6 text-slate-600">
                        {test.rationale}
                      </p>
                    </article>
                  ),
                )}
              </div>
            ) : (
              <EmptyMessage />
            )}
          </Section>
  
          <Section title="Initial management">
            {result.initial_management.length > 0 ? (
              <ol className="space-y-4">
                {result.initial_management.map(
                  (item, index) => (
                    <li
                      key={`${item.recommendation}-${index}`}
                      className="flex gap-3"
                    >
                      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
                        {index + 1}
                      </span>
  
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {item.recommendation}
                        </p>
  
                        {item.rationale ? (
                          <p className="mt-1 text-sm leading-6 text-slate-600">
                            {item.rationale}
                          </p>
                        ) : null}
                      </div>
                    </li>
                  ),
                )}
              </ol>
            ) : (
              <EmptyMessage />
            )}
          </Section>
        </div>
  
        {result.red_flags.length > 0 ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-6">
            <h3 className="font-semibold text-red-950">
              Red flags
            </h3>
  
            <ul className="mt-4 space-y-2">
              {result.red_flags.map((item) => (
                <li
                  key={item}
                  className="flex gap-3 text-sm leading-6 text-red-900"
                >
                  <span aria-hidden="true">
                    !
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
  
        {result.limitations.length > 0 ? (
          <Section title="Limitations">
            <ul className="space-y-2">
              {result.limitations.map((item) => (
                <li
                  key={item}
                  className="text-sm leading-6 text-slate-600"
                >
                  {item}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}
  
        {result.trace_id ? (
          <p className="font-mono text-xs text-slate-500">
            Trace ID: {result.trace_id}
          </p>
        ) : null}
      </div>
    );
  }