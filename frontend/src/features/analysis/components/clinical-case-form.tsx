"use client";

import {
  useActionState,
  useState,
} from "react";

import { submitClinicalCase } from "@/features/analysis/actions/submit-clinical-case";
import {
  createEmptyClinicalCase,
  createExampleClinicalCase,
  initialClinicalCaseFormState,
  type ClinicalCase,
  type LaboratoryResult,
  type Medication,
  type PatientSex,
} from "@/features/analysis/types/analysis";

import { StructuredAnalysisResultView } from "./structured-analysis-result";

const inputClassName = [
  "mt-2 block w-full rounded-xl border",
  "border-slate-300 bg-white px-3 py-2.5",
  "text-sm text-slate-950 outline-none transition",
  "placeholder:text-slate-400",
  "focus:border-slate-500 focus:ring-4",
  "focus:ring-slate-100",
].join(" ");

const labelClassName =
  "block text-sm font-semibold text-slate-900";

function createId(): string {
  return crypto.randomUUID();
}

function cloneCase(
    clinicalCase: ClinicalCase,
  ): ClinicalCase {
    return JSON.parse(
      JSON.stringify(clinicalCase),
    ) as ClinicalCase;
  }

function parseOptionalNumber(
  value: string,
): number | null {
  if (!value.trim()) {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : null;
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-950">
          {title}
        </h2>

        {description ? (
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {description}
          </p>
        ) : null}
      </div>

      <div className="mt-6">
        {children}
      </div>
    </section>
  );
}

function StringListEditor({
  label,
  values,
  placeholder,
  onChange,
}: {
  label: string;
  values: string[];
  placeholder: string;
  onChange: (values: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  function addValue() {
    const value = draft.trim();

    if (!value) {
      return;
    }

    onChange([...values, value]);
    setDraft("");
  }

  return (
    <div>
      <label className={labelClassName}>
        {label}
      </label>

      <div className="mt-2 flex gap-2">
        <input
          value={draft}
          onChange={(event) =>
            setDraft(event.target.value)
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addValue();
            }
          }}
          placeholder={placeholder}
          className={[
            inputClassName,
            "mt-0",
          ].join(" ")}
        />

        <button
          type="button"
          onClick={addValue}
          className="shrink-0 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Add
        </button>
      </div>

      {values.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {values.map((value, index) => (
            <span
              key={`${value}-${index}`}
              className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-700"
            >
              {value}

              <button
                type="button"
                onClick={() =>
                  onChange(
                    values.filter(
                      (_, itemIndex) =>
                        itemIndex !== index,
                    ),
                  )
                }
                aria-label={`Remove ${value}`}
                className="font-semibold text-slate-500 hover:text-slate-950"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-xs text-slate-500">
          No entries added.
        </p>
      )}
    </div>
  );
}

export function ClinicalCaseForm() {
  const [clinicalCase, setClinicalCase] =
    useState<ClinicalCase>(
      (createEmptyClinicalCase),
    );

  const [state, formAction, isPending] =
    useActionState(
      submitClinicalCase,
      initialClinicalCaseFormState,
    );

    function loadSyntheticExample() {
        setClinicalCase(
          createExampleClinicalCase(),
        );
      }
      
      function clearClinicalCase() {
        setClinicalCase(
          createEmptyClinicalCase(),
        );
      }

  function updateCase(
    updater: (
      current: ClinicalCase,
    ) => ClinicalCase,
  ) {
    setClinicalCase((current) =>
      updater(cloneCase(current)),
    );
  }

  function addMedication() {
    const medication: Medication = {
      id: createId(),
      name: "",
      dose: "",
      frequency: "",
    };

    updateCase((current) => {
      current.medications.push(medication);
      return current;
    });
  }

  function updateMedication(
    id: string,
    field: keyof Omit<Medication, "id">,
    value: string,
  ) {
    updateCase((current) => {
      const medication =
        current.medications.find(
          (item) => item.id === id,
        );

      if (medication) {
        medication[field] = value;
      }

      return current;
    });
  }

  function addLaboratoryResult() {
    const laboratoryResult: LaboratoryResult = {
      id: createId(),
      test_name: "",
      value: "",
      unit: "",
      reference_range: "",
    };

    updateCase((current) => {
      current.laboratory_results.push(
        laboratoryResult,
      );

      return current;
    });
  }

  function updateLaboratoryResult(
    id: string,
    field: keyof Omit<
      LaboratoryResult,
      "id"
    >,
    value: string,
  ) {
    updateCase((current) => {
      const result =
        current.laboratory_results.find(
          (item) => item.id === id,
        );

      if (result) {
        result[field] = value;
      }

      return current;
    });
  }

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
        <h2 className="font-semibold text-blue-950">
          De-identified development data only
        </h2>

        <p className="mt-2 text-sm leading-6 text-blue-900">
          Use only synthetic or properly de-identified
          information. Do not enter names, dates of
          birth, addresses, medical record numbers, or
          other protected health information.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Structured case builder
          </p>

          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
            New clinical case
          </h2>
        </div>

        <div className="flex flex-wrap gap-2">
            <button
                type="button"
                onClick={loadSyntheticExample}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
                Load synthetic example
            </button>

            <button
                type="button"
                onClick={clearClinicalCase}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
                Clear case
            </button>
        </div>
      </div>

      <form
        action={formAction}
        className="space-y-6"
      >
        <input
          type="hidden"
          name="clinicalCase"
          value={JSON.stringify(clinicalCase)}
          readOnly
        />

        <Section
          title="Patient information"
          description="Use general demographic information only."
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label
                htmlFor="patient-age"
                className={labelClassName}
              >
                Age
              </label>

              <input
                id="patient-age"
                type="number"
                min={0}
                max={130}
                value={
                  clinicalCase.patient.age ?? ""
                }
                onChange={(event) =>
                  updateCase((current) => {
                    current.patient.age =
                      parseOptionalNumber(
                        event.target.value,
                      );

                    return current;
                  })
                }
                className={inputClassName}
              />
            </div>

            <div>
              <label
                htmlFor="patient-sex"
                className={labelClassName}
              >
                Sex
              </label>

              <select
                id="patient-sex"
                value={clinicalCase.patient.sex}
                onChange={(event) =>
                  updateCase((current) => {
                    current.patient.sex =
                      event.target
                        .value as PatientSex;

                    return current;
                  })
                }
                className={inputClassName}
              >
                <option value="unknown">
                  Unknown
                </option>
                <option value="female">
                  Female
                </option>
                <option value="male">
                  Male
                </option>
                <option value="intersex">
                  Intersex
                </option>
                <option value="other">
                  Other
                </option>
              </select>
            </div>
          </div>
        </Section>

        <Section title="Clinical presentation">
          <div className="space-y-6">
            <div>
              <label
                htmlFor="chief-complaint"
                className={labelClassName}
              >
                Chief complaint
              </label>

              <textarea
                id="chief-complaint"
                rows={3}
                value={
                  clinicalCase.chief_complaint
                }
                onChange={(event) =>
                  updateCase((current) => {
                    current.chief_complaint =
                      event.target.value;

                    return current;
                  })
                }
                placeholder="Primary reason for presentation"
                className={inputClassName}
              />
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="duration"
                  className={labelClassName}
                >
                  Duration
                </label>

                <input
                  id="duration"
                  value={
                    clinicalCase
                      .history_of_present_illness
                      .duration
                  }
                  onChange={(event) =>
                    updateCase((current) => {
                      current.history_of_present_illness.duration =
                        event.target.value;

                      return current;
                    })
                  }
                  placeholder="Example: 3 days"
                  className={inputClassName}
                />
              </div>

              <div>
                <label
                  htmlFor="severity"
                  className={labelClassName}
                >
                  Course or severity
                </label>

                <input
                  id="severity"
                  value={
                    clinicalCase
                      .history_of_present_illness
                      .severity
                  }
                  onChange={(event) =>
                    updateCase((current) => {
                      current.history_of_present_illness.severity =
                        event.target.value;

                      return current;
                    })
                  }
                  placeholder="Example: Worsening"
                  className={inputClassName}
                />
              </div>
            </div>

            <StringListEditor
              label="Symptoms"
              values={
                clinicalCase
                  .history_of_present_illness
                  .symptoms
              }
              placeholder="Add a symptom"
              onChange={(values) =>
                updateCase((current) => {
                  current.history_of_present_illness.symptoms =
                    values;

                  return current;
                })
              }
            />
          </div>
        </Section>

        <Section title="Relevant history">
          <div className="space-y-6">
            <StringListEditor
              label="Medical history"
              values={
                clinicalCase.medical_history
              }
              placeholder="Add a medical condition"
              onChange={(values) =>
                updateCase((current) => {
                  current.medical_history =
                    values;

                  return current;
                })
              }
            />

            <StringListEditor
              label="Allergies"
              values={clinicalCase.allergies}
              placeholder="Add an allergy"
              onChange={(values) =>
                updateCase((current) => {
                  current.allergies = values;
                  return current;
                })
              }
            />

            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="smoking-status"
                  className={labelClassName}
                >
                  Smoking status
                </label>

                <input
                  id="smoking-status"
                  value={
                    clinicalCase.social_history
                      .smoking_status
                  }
                  onChange={(event) =>
                    updateCase((current) => {
                      current.social_history.smoking_status =
                        event.target.value;

                      return current;
                    })
                  }
                  className={inputClassName}
                />
              </div>

              <div>
                <label
                  htmlFor="pack-years"
                  className={labelClassName}
                >
                  Pack-years
                </label>

                <input
                  id="pack-years"
                  type="number"
                  min={0}
                  value={
                    clinicalCase.social_history
                      .pack_years ?? ""
                  }
                  onChange={(event) =>
                    updateCase((current) => {
                      current.social_history.pack_years =
                        parseOptionalNumber(
                          event.target.value,
                        );

                      return current;
                    })
                  }
                  className={inputClassName}
                />
              </div>
            </div>
          </div>
        </Section>

        <Section title="Current medications">
          <div className="space-y-4">
            {clinicalCase.medications.map(
              (medication) => (
                <div
                  key={medication.id}
                  className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1fr_0.7fr_0.8fr_auto]"
                >
                  <input
                    aria-label="Medication name"
                    value={medication.name}
                    onChange={(event) =>
                      updateMedication(
                        medication.id,
                        "name",
                        event.target.value,
                      )
                    }
                    placeholder="Medication"
                    className={[
                      inputClassName,
                      "mt-0",
                    ].join(" ")}
                  />

                  <input
                    aria-label="Medication dose"
                    value={medication.dose}
                    onChange={(event) =>
                      updateMedication(
                        medication.id,
                        "dose",
                        event.target.value,
                      )
                    }
                    placeholder="Dose"
                    className={[
                      inputClassName,
                      "mt-0",
                    ].join(" ")}
                  />

                  <input
                    aria-label="Medication frequency"
                    value={medication.frequency}
                    onChange={(event) =>
                      updateMedication(
                        medication.id,
                        "frequency",
                        event.target.value,
                      )
                    }
                    placeholder="Frequency"
                    className={[
                      inputClassName,
                      "mt-0",
                    ].join(" ")}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      updateCase((current) => {
                        current.medications =
                          current.medications.filter(
                            (item) =>
                              item.id !==
                              medication.id,
                          );

                        return current;
                      })
                    }
                    className="rounded-xl border border-red-200 px-3 text-sm font-semibold text-red-700 hover:bg-red-50"
                  >
                    Remove
                  </button>
                </div>
              ),
            )}

            <button
              type="button"
              onClick={addMedication}
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Add medication
            </button>
          </div>
        </Section>

        <Section title="Vital signs">
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                key: "temperature_celsius",
                label: "Temperature (°C)",
              },
              {
                key: "heart_rate_bpm",
                label: "Heart rate (bpm)",
              },
              {
                key: "respiratory_rate_bpm",
                label: "Respiratory rate",
              },
              {
                key: "oxygen_saturation_percent",
                label: "Oxygen saturation (%)",
              },
            ].map((field) => (
              <div key={field.key}>
                <label
                  htmlFor={field.key}
                  className={labelClassName}
                >
                  {field.label}
                </label>

                <input
                  id={field.key}
                  type="number"
                  step="any"
                  value={
                    clinicalCase.vital_signs[
                      field.key as keyof Pick<
                        typeof clinicalCase.vital_signs,
                        | "temperature_celsius"
                        | "heart_rate_bpm"
                        | "respiratory_rate_bpm"
                        | "oxygen_saturation_percent"
                      >
                    ] ?? ""
                  }
                  onChange={(event) =>
                    updateCase((current) => {
                      const key =
                        field.key as
                          | "temperature_celsius"
                          | "heart_rate_bpm"
                          | "respiratory_rate_bpm"
                          | "oxygen_saturation_percent";

                      current.vital_signs[key] =
                        parseOptionalNumber(
                          event.target.value,
                        );

                      return current;
                    })
                  }
                  className={inputClassName}
                />
              </div>
            ))}

            <div>
              <label
                htmlFor="blood-pressure"
                className={labelClassName}
              >
                Blood pressure
              </label>

              <input
                id="blood-pressure"
                value={
                  clinicalCase.vital_signs
                    .blood_pressure_mmHg
                }
                onChange={(event) =>
                  updateCase((current) => {
                    current.vital_signs.blood_pressure_mmHg =
                      event.target.value;

                    return current;
                  })
                }
                placeholder="132/78"
                className={inputClassName}
              />
            </div>

            <div>
              <label
                htmlFor="oxygen-support"
                className={labelClassName}
              >
                Oxygen support
              </label>

              <input
                id="oxygen-support"
                value={
                  clinicalCase.vital_signs
                    .oxygen_support
                }
                onChange={(event) =>
                  updateCase((current) => {
                    current.vital_signs.oxygen_support =
                      event.target.value;

                    return current;
                  })
                }
                placeholder="Room air"
                className={inputClassName}
              />
            </div>
          </div>
        </Section>

        <Section title="Physical examination">
          <div className="space-y-6">
            <div>
              <label
                htmlFor="general-exam"
                className={labelClassName}
              >
                General appearance
              </label>

              <textarea
                id="general-exam"
                rows={3}
                value={
                  clinicalCase.physical_exam
                    .general
                }
                onChange={(event) =>
                  updateCase((current) => {
                    current.physical_exam.general =
                      event.target.value;

                    return current;
                  })
                }
                className={inputClassName}
              />
            </div>

            <StringListEditor
              label="Respiratory findings"
              values={
                clinicalCase.physical_exam
                  .respiratory
              }
              placeholder="Add respiratory finding"
              onChange={(values) =>
                updateCase((current) => {
                  current.physical_exam.respiratory =
                    values;

                  return current;
                })
              }
            />

            <StringListEditor
              label="Cardiovascular findings"
              values={
                clinicalCase.physical_exam
                  .cardiovascular
              }
              placeholder="Add cardiovascular finding"
              onChange={(values) =>
                updateCase((current) => {
                  current.physical_exam.cardiovascular =
                    values;

                  return current;
                })
              }
            />
          </div>
        </Section>

        <Section title="Laboratory results">
          <div className="space-y-4">
            {clinicalCase.laboratory_results.map(
              (result) => (
                <div
                  key={result.id}
                  className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1.2fr_0.6fr_0.6fr_0.8fr_auto]"
                >
                  {(
                    [
                      [
                        "test_name",
                        "Test name",
                      ],
                      ["value", "Value"],
                      ["unit", "Unit"],
                      [
                        "reference_range",
                        "Reference range",
                      ],
                    ] as const
                  ).map(([field, placeholder]) => (
                    <input
                      key={field}
                      aria-label={placeholder}
                      value={result[field]}
                      onChange={(event) =>
                        updateLaboratoryResult(
                          result.id,
                          field,
                          event.target.value,
                        )
                      }
                      placeholder={placeholder}
                      className={[
                        inputClassName,
                        "mt-0",
                      ].join(" ")}
                    />
                  ))}

                  <button
                    type="button"
                    onClick={() =>
                      updateCase((current) => {
                        current.laboratory_results =
                          current.laboratory_results.filter(
                            (item) =>
                              item.id !==
                              result.id,
                          );

                        return current;
                      })
                    }
                    className="rounded-xl border border-red-200 px-3 text-sm font-semibold text-red-700 hover:bg-red-50"
                  >
                    Remove
                  </button>
                </div>
              ),
            )}

            <button
              type="button"
              onClick={addLaboratoryResult}
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Add laboratory result
            </button>
          </div>
        </Section>

        <Section title="Imaging">
          <div className="space-y-4">
            {clinicalCase.imaging.map(
              (study) => (
                <div
                  key={study.id}
                  className="rounded-xl border border-slate-200 p-4"
                >
                  <div className="flex items-start gap-3">
                    <input
                      aria-label="Imaging type"
                      value={study.type}
                      onChange={(event) =>
                        updateCase((current) => {
                          const currentStudy =
                            current.imaging.find(
                              (item) =>
                                item.id === study.id,
                            );

                          if (currentStudy) {
                            currentStudy.type =
                              event.target.value;
                          }

                          return current;
                        })
                      }
                      placeholder="Imaging type"
                      className={[
                        inputClassName,
                        "mt-0",
                      ].join(" ")}
                    />

                    <button
                      type="button"
                      onClick={() =>
                        updateCase((current) => {
                          current.imaging =
                            current.imaging.filter(
                              (item) =>
                                item.id !==
                                study.id,
                            );

                          return current;
                        })
                      }
                      className="rounded-xl border border-red-200 px-3 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-50"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="mt-4">
                    <StringListEditor
                      label="Findings"
                      values={study.findings}
                      placeholder="Add imaging finding"
                      onChange={(values) =>
                        updateCase((current) => {
                          const currentStudy =
                            current.imaging.find(
                              (item) =>
                                item.id === study.id,
                            );

                          if (currentStudy) {
                            currentStudy.findings =
                              values;
                          }

                          return current;
                        })
                      }
                    />
                  </div>
                </div>
              ),
            )}

            <button
              type="button"
              onClick={() =>
                updateCase((current) => {
                  current.imaging.push({
                    id: createId(),
                    type: "",
                    findings: [],
                  });

                  return current;
                })
              }
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Add imaging study
            </button>
          </div>
        </Section>

        <Section title="Clinical questions">
          <StringListEditor
            label="Questions for CareLens"
            values={
              clinicalCase.clinical_question
            }
            placeholder="Add a clinical question"
            onChange={(values) =>
              updateCase((current) => {
                current.clinical_question =
                  values;

                return current;
              })
            }
          />
        </Section>

        {state.status ===
        "validation_error" ? (
          <div
            role="alert"
            className="rounded-2xl border border-amber-200 bg-amber-50 p-5"
          >
            <p className="font-semibold text-amber-950">
              Review the clinical case
            </p>

            <p className="mt-2 text-sm leading-6 text-amber-900">
              {state.message}
            </p>
          </div>
        ) : null}

        {state.status === "error" ? (
          <div
            role="alert"
            className="rounded-2xl border border-red-200 bg-red-50 p-5"
          >
            <p className="font-semibold text-red-950">
              Analysis failed
            </p>

            <p className="mt-2 text-sm leading-6 text-red-900">
              {state.message}
            </p>

            {state.traceId ? (
              <p className="mt-3 font-mono text-xs text-red-700">
                Trace ID: {state.traceId}
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="sticky bottom-4 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Ready to analyze
            </p>

            <p className="text-xs text-slate-500">
              Review the case for protected health
              information before submission.
            </p>
          </div>

          <button
            type="submit"
            disabled={isPending}
            className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isPending
              ? "Analyzing case…"
              : "Analyze clinical case"}
          </button>
        </div>
      </form>

      {state.status === "success" ? (
        <StructuredAnalysisResultView
          result={state.result}
        />
      ) : null}
    </div>
  );
}