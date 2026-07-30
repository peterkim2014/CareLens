import "server-only";

import { apiRequest } from "@/lib/api/client";

import type {
  ClinicalCase,
  StructuredAnalysisResult,
} from "../types/analysis";

interface AnalysisRequest {
  text: string;
}

type UnknownRecord =
  Record<string, unknown>;

function isRecord(
  value: unknown,
): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getString(
  value: unknown,
): string | null {
  return typeof value === "string"
    ? value
    : null;
}

function getNumber(
  value: unknown,
): number | null {
  return (
    typeof value === "number" &&
    Number.isFinite(value)
  )
    ? value
    : null;
}

function getBoolean(
  value: unknown,
): boolean | null {
  return typeof value === "boolean"
    ? value
    : null;
}

function getStringArray(
  value: unknown,
): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(
    (item): item is string =>
      typeof item === "string",
  );
}

function getNestedValue(
  value: unknown,
  keys: string[],
): unknown {
  let current: unknown = value;

  for (const key of keys) {
    if (!isRecord(current)) {
      return undefined;
    }

    current = current[key];
  }

  return current;
}

function getNestedString(
  value: unknown,
  keys: string[],
): string | null {
  return getString(
    getNestedValue(value, keys),
  );
}

function getNestedNumber(
  value: unknown,
  keys: string[],
): number | null {
  return getNumber(
    getNestedValue(value, keys),
  );
}

function unwrapResponse(
  response: UnknownRecord,
): UnknownRecord {
  const candidates = [
    response.data,
    response.result,
    response.analysis,
    response.payload,
  ];

  for (const candidate of candidates) {
    if (isRecord(candidate)) {
      return candidate;
    }
  }

  return response;
}

function uniqueStrings(
  values: string[],
): string[] {
  return Array.from(
    new Set(
      values
        .map((value) => value.trim())
        .filter(Boolean),
    ),
  );
}

function extractSignalLabels(
  value: unknown,
): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((signal) => {
      if (!isRecord(signal)) {
        return null;
      }

      const label =
        getString(signal.label);

      const matchedPhrase =
        getString(
          signal.matched_phrase,
        );

      if (
        label &&
        matchedPhrase
      ) {
        return `${label}: "${matchedPhrase}"`;
      }

      return label ?? matchedPhrase;
    })
    .filter(
      (value): value is string =>
        value !== null,
    );
}

function isEmergencyResponse(
  payload: UnknownRecord,
): boolean {
  const disposition =
    getString(payload.disposition);

  const riskLevel =
    getNestedString(
      payload,
      [
        "risk_assessment",
        "risk_level",
      ],
    );

  const routingAction =
    getNestedString(
      payload,
      [
        "risk_assessment",
        "routing_action",
      ],
    );

  const responseKind =
    getNestedString(
      payload,
      [
        "user_response",
        "kind",
      ],
    );

  const canContinue =
    getBoolean(
      getNestedValue(
        payload,
        [
          "user_response",
          "can_continue",
        ],
      ),
    );

  return (
    disposition ===
      "halted_emergency" ||
    riskLevel === "emergency" ||
    routingAction ===
      "seek_emergency_care" ||
    responseKind === "emergency" ||
    canContinue === false
  );
}

function normalizeEmergencyResult(
  payload: UnknownRecord,
  response: UnknownRecord,
): StructuredAnalysisResult {
  const riskAssessment =
    isRecord(
      payload.risk_assessment,
    )
      ? payload.risk_assessment
      : {};

  const userResponse =
    isRecord(payload.user_response)
      ? payload.user_response
      : {};

  const emergencyMessage =
    getString(
      riskAssessment.emergency_message,
    ) ??
    getString(userResponse.message) ??
    "The submitted case contains emergency warning signs. Seek immediate medical care.";

  const reasoning =
    uniqueStrings([
      ...getStringArray(
        riskAssessment.reasoning,
      ),
      emergencyMessage,
    ]);

  const recommendedActions =
    getStringArray(
      userResponse.recommended_actions,
    );

  const signalLabels =
    extractSignalLabels(
      riskAssessment.signals,
    );

  const redFlags =
    uniqueStrings([
      ...signalLabels,
      ...getStringArray(
        riskAssessment.red_flags,
      ),
      ...getStringArray(
        riskAssessment.warning_signs,
      ),
    ]);

  const traceId =
    getString(payload.trace_id) ??
    getString(response.trace_id) ??
    undefined;

  return {
    most_likely_diagnosis: {
      name:
        "Emergency warning signs detected",
      confidence: null,
      reasoning:
        reasoning.length > 0
          ? reasoning
          : [
              "The safety system stopped automated diagnostic analysis because emergency warning signs were detected.",
            ],
    },

    differential_diagnoses: [],

    supporting_evidence:
      signalLabels.length > 0
        ? signalLabels
        : [
            "The safety assessment classified this case as an emergency.",
          ],

    recommended_tests: [],

    initial_management:
      recommendedActions.map(
        (action) => ({
          recommendation: action,
          rationale:
            "Recommended by the emergency safety-routing response.",
        }),
      ),

    red_flags:
      redFlags.length > 0
        ? redFlags
        : [
            "Emergency-level symptoms were detected.",
          ],

    limitations: [
      "Diagnostic analysis was intentionally stopped so it would not delay emergency medical care.",
      "No diagnosis, differential diagnosis, retrieval, or treatment recommendation was generated.",
      "This application is not a substitute for emergency medical services.",
    ],

    trace_id: traceId,
  };
}

function extractNarrative(
  payload: UnknownRecord,
): string {
  const directCandidates = [
    payload.user_response,
    payload.grounded_response,
    payload.response,
    payload.answer,
    payload.analysis,
    payload.content,
    payload.summary,
    payload.message,
  ];

  for (const candidate of directCandidates) {
    if (
      typeof candidate === "string"
    ) {
      return candidate;
    }
  }

  const nestedCandidates = [
    ["user_response", "message"],
    ["user_response", "text"],
    ["user_response", "content"],
    ["grounded_response", "text"],
    [
      "grounded_response",
      "content",
    ],
    ["grounded_response", "answer"],
    ["response", "text"],
    ["response", "content"],
    ["response", "answer"],
    ["analysis", "text"],
    ["analysis", "content"],
    ["analysis", "answer"],
  ];

  for (
    const path of nestedCandidates
  ) {
    const candidate =
      getNestedString(
        payload,
        path,
      );

    if (candidate) {
      return candidate;
    }
  }

  return "";
}

function extractDiagnosisName(
  payload: UnknownRecord,
): string {
  const candidates = [
    getNestedString(
      payload,
      [
        "most_likely_diagnosis",
        "name",
      ],
    ),
    getNestedString(
      payload,
      [
        "most_likely_diagnosis",
        "diagnosis",
      ],
    ),
    getNestedString(
      payload,
      ["diagnosis", "name"],
    ),
    getNestedString(
      payload,
      ["diagnosis", "diagnosis"],
    ),
    getString(payload.diagnosis),
    getString(
      payload.most_likely_diagnosis,
    ),
    getString(
      payload.primary_diagnosis,
    ),
    getNestedString(
      payload,
      [
        "clinical_impression",
        "diagnosis",
      ],
    ),
    getNestedString(
      payload,
      [
        "clinical_impression",
        "name",
      ],
    ),
  ];

  for (const candidate of candidates) {
    if (candidate) {
      return candidate;
    }
  }

  return "Clinical analysis completed";
}

function extractConfidence(
  payload: UnknownRecord,
): number | null {
  const candidates = [
    getNestedNumber(
      payload,
      [
        "most_likely_diagnosis",
        "confidence",
      ],
    ),
    getNestedNumber(
      payload,
      [
        "diagnosis",
        "confidence",
      ],
    ),
    getNestedNumber(
      payload,
      [
        "clinical_impression",
        "confidence",
      ],
    ),
    getNumber(payload.confidence),
  ];

  for (const candidate of candidates) {
    if (candidate !== null) {
      return candidate;
    }
  }

  return null;
}

function extractReasoning(
  payload: UnknownRecord,
): string[] {
  const candidates = [
    getNestedValue(
      payload,
      [
        "most_likely_diagnosis",
        "reasoning",
      ],
    ),
    getNestedValue(
      payload,
      [
        "diagnosis",
        "reasoning",
      ],
    ),
    getNestedValue(
      payload,
      [
        "clinical_impression",
        "reasoning",
      ],
    ),
    payload.reasoning,
    payload.supporting_evidence,
  ];

  for (const candidate of candidates) {
    const arrayValue =
      getStringArray(candidate);

    if (arrayValue.length > 0) {
      return arrayValue;
    }

    const stringValue =
      getString(candidate);

    if (stringValue) {
      return [stringValue];
    }
  }

  const narrative =
    extractNarrative(payload);

  return narrative
    ? [narrative]
    : [
        "The backend completed the analysis but did not return structured diagnostic reasoning.",
      ];
}

function normalizeDifferentialDiagnoses(
  value: unknown,
): StructuredAnalysisResult["differential_diagnoses"] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (
        typeof item === "string"
      ) {
        return {
          name: item,
          reasoning: "",
        };
      }

      if (!isRecord(item)) {
        return null;
      }

      const name =
        getString(item.name) ??
        getString(item.diagnosis) ??
        getString(item.condition);

      if (!name) {
        return null;
      }

      return {
        name,
        reasoning:
          getString(item.reasoning) ??
          getString(item.rationale) ??
          getString(
            item.explanation,
          ) ??
          "",
        urgency:
          getString(item.urgency) ??
          getString(item.priority) ??
          undefined,
      };
    })
    .filter(
      (
        item,
      ): item is NonNullable<
        typeof item
      > => item !== null,
    );
}

function normalizeRecommendedTests(
  value: unknown,
): StructuredAnalysisResult["recommended_tests"] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (
        typeof item === "string"
      ) {
        return {
          name: item,
          rationale: "",
        };
      }

      if (!isRecord(item)) {
        return null;
      }

      const name =
        getString(item.name) ??
        getString(item.test) ??
        getString(item.test_name);

      if (!name) {
        return null;
      }

      return {
        name,
        rationale:
          getString(item.rationale) ??
          getString(item.reasoning) ??
          getString(
            item.explanation,
          ) ??
          "",
        priority:
          getString(item.priority) ??
          getString(item.urgency) ??
          undefined,
      };
    })
    .filter(
      (
        item,
      ): item is NonNullable<
        typeof item
      > => item !== null,
    );
}

function normalizeInitialManagement(
  value: unknown,
): StructuredAnalysisResult["initial_management"] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (
        typeof item === "string"
      ) {
        return {
          recommendation: item,
        };
      }

      if (!isRecord(item)) {
        return null;
      }

      const recommendation =
        getString(
          item.recommendation,
        ) ??
        getString(item.action) ??
        getString(item.treatment) ??
        getString(
          item.intervention,
        );

      if (!recommendation) {
        return null;
      }

      return {
        recommendation,
        rationale:
          getString(item.rationale) ??
          getString(item.reasoning) ??
          getString(
            item.explanation,
          ) ??
          undefined,
      };
    })
    .filter(
      (
        item,
      ): item is NonNullable<
        typeof item
      > => item !== null,
    );
}

function normalizeStructuredResult(
  response: unknown,
): StructuredAnalysisResult {
  if (!isRecord(response)) {
    throw new Error(
      "The backend returned an invalid response.",
    );
  }

  const payload =
    unwrapResponse(response);

  if (
    isEmergencyResponse(payload)
  ) {
    return normalizeEmergencyResult(
      payload,
      response,
    );
  }

  const diagnosis =
    isRecord(
      payload.most_likely_diagnosis,
    )
      ? payload.most_likely_diagnosis
      : null;

  const riskAssessment =
    isRecord(
      payload.risk_assessment,
    )
      ? payload.risk_assessment
      : null;

  const disposition =
    isRecord(payload.disposition)
      ? payload.disposition
      : null;

  const supportingEvidence = [
    ...getStringArray(
      payload.supporting_evidence,
    ),
    ...getStringArray(
      diagnosis?.supporting_evidence,
    ),
  ];

  const riskReasoning =
    getStringArray(
      riskAssessment?.reasoning,
    );

  supportingEvidence.push(
    ...riskReasoning,
  );

  const riskExplanation =
    getString(
      riskAssessment?.explanation,
    ) ??
    getString(
      riskAssessment?.rationale,
    );

  const dispositionRationale =
    getString(
      disposition?.rationale,
    ) ??
    getString(
      disposition?.explanation,
    );

  if (riskExplanation) {
    supportingEvidence.push(
      riskExplanation,
    );
  }

  if (dispositionRationale) {
    supportingEvidence.push(
      dispositionRationale,
    );
  }

  const redFlags =
    uniqueStrings([
      ...getStringArray(
        payload.red_flags,
      ),
      ...getStringArray(
        riskAssessment?.red_flags,
      ),
      ...getStringArray(
        riskAssessment?.warning_signs,
      ),
      ...extractSignalLabels(
        riskAssessment?.signals,
      ),
    ]);

  const limitations =
    getStringArray(
      payload.limitations,
    );

  if (
    limitations.length === 0 &&
    !isRecord(
      payload.most_likely_diagnosis,
    )
  ) {
    limitations.push(
      "The backend response used a legacy analysis schema and was adapted for display.",
    );
  }

  const differentialDiagnoses =
    normalizeDifferentialDiagnoses(
      payload.differential_diagnoses ??
        payload.differentials ??
        payload.differential,
    );

  const recommendedTests =
    normalizeRecommendedTests(
      payload.recommended_tests ??
        payload.tests ??
        payload.additional_tests,
    );

  const initialManagement =
    normalizeInitialManagement(
      payload.initial_management ??
        payload.management ??
        payload.treatment_plan ??
        payload.recommendations,
    );

  const traceId =
    getString(payload.trace_id) ??
    getString(response.trace_id) ??
    undefined;

  return {
    most_likely_diagnosis: {
      name:
        extractDiagnosisName(
          payload,
        ),
      confidence:
        extractConfidence(payload),
      reasoning:
        extractReasoning(payload),
    },

    differential_diagnoses:
      differentialDiagnoses,

    supporting_evidence:
      uniqueStrings(
        supportingEvidence,
      ),

    recommended_tests:
      recommendedTests,

    initial_management:
      initialManagement,

    red_flags: redFlags,

    limitations,

    trace_id: traceId,
  };
}

function formatList(
  title: string,
  values: string[],
): string {
  if (values.length === 0) {
    return "";
  }

  return [
    `${title}:`,
    ...values.map(
      (value) => `- ${value}`,
    ),
  ].join("\n");
}

function formatClinicalCase(
  clinicalCase: ClinicalCase,
): string {
  const sections: string[] = [];

  const patientDescription = [
    clinicalCase.patient.age !== null
      ? `${clinicalCase.patient.age}-year-old`
      : "Age unspecified",
    clinicalCase.patient.sex !==
    "unknown"
      ? clinicalCase.patient.sex
      : "sex unspecified",
  ].join(" ");

  sections.push(
    `Patient:\n${patientDescription}`,
  );

  sections.push(
    [
      "Chief complaint:",
      clinicalCase.chief_complaint,
    ].join("\n"),
  );

  const historyLines = [
    clinicalCase
      .history_of_present_illness
      .duration
      ? `Duration: ${clinicalCase.history_of_present_illness.duration}`
      : "",
    clinicalCase
      .history_of_present_illness
      .severity
      ? `Course/severity: ${clinicalCase.history_of_present_illness.severity}`
      : "",
    formatList(
      "Symptoms",
      clinicalCase
        .history_of_present_illness
        .symptoms,
    ),
  ].filter(Boolean);

  if (historyLines.length > 0) {
    sections.push(
      [
        "History of present illness:",
        ...historyLines,
      ].join("\n"),
    );
  }

  if (
    clinicalCase.medical_history
      .length > 0
  ) {
    sections.push(
      formatList(
        "Relevant medical history",
        clinicalCase.medical_history,
      ),
    );
  }

  const socialHistory = [
    clinicalCase.social_history
      .smoking_status,
    clinicalCase.social_history
      .pack_years !== null
      ? `${clinicalCase.social_history.pack_years} pack-years`
      : "",
  ]
    .filter(Boolean)
    .join(", ");

  if (socialHistory) {
    sections.push(
      `Social history:\n${socialHistory}`,
    );
  }

  if (
    clinicalCase.medications.length >
    0
  ) {
    sections.push(
      [
        "Current medications:",
        ...clinicalCase.medications.map(
          (medication) =>
            `- ${[
              medication.name,
              medication.dose,
              medication.frequency,
            ]
              .filter(Boolean)
              .join(" — ")}`,
        ),
      ].join("\n"),
    );
  }

  sections.push(
    clinicalCase.allergies.length > 0
      ? formatList(
          "Allergies",
          clinicalCase.allergies,
        )
      : "Allergies:\n- No known allergies reported",
  );

  const vitalSigns = [
    clinicalCase.vital_signs
      .temperature_celsius !== null
      ? `Temperature: ${clinicalCase.vital_signs.temperature_celsius} °C`
      : "",
    clinicalCase.vital_signs
      .heart_rate_bpm !== null
      ? `Heart rate: ${clinicalCase.vital_signs.heart_rate_bpm} bpm`
      : "",
    clinicalCase.vital_signs
      .blood_pressure_mmHg
      ? `Blood pressure: ${clinicalCase.vital_signs.blood_pressure_mmHg} mmHg`
      : "",
    clinicalCase.vital_signs
      .respiratory_rate_bpm !== null
      ? `Respiratory rate: ${clinicalCase.vital_signs.respiratory_rate_bpm} breaths/min`
      : "",
    clinicalCase.vital_signs
      .oxygen_saturation_percent !==
    null
      ? `Oxygen saturation: ${clinicalCase.vital_signs.oxygen_saturation_percent}%`
      : "",
    clinicalCase.vital_signs
      .oxygen_support
      ? `Oxygen support: ${clinicalCase.vital_signs.oxygen_support}`
      : "",
  ].filter(Boolean);

  if (vitalSigns.length > 0) {
    sections.push(
      [
        "Vital signs:",
        ...vitalSigns.map(
          (value) => `- ${value}`,
        ),
      ].join("\n"),
    );
  }

  const examination = [
    clinicalCase.physical_exam.general
      ? `General: ${clinicalCase.physical_exam.general}`
      : "",
    formatList(
      "Respiratory",
      clinicalCase.physical_exam
        .respiratory,
    ),
    formatList(
      "Cardiovascular",
      clinicalCase.physical_exam
        .cardiovascular,
    ),
    formatList(
      "Neurologic",
      clinicalCase.physical_exam
        .neurologic,
    ),
    formatList(
      "Abdominal",
      clinicalCase.physical_exam
        .abdominal,
    ),
    formatList(
      "Other",
      clinicalCase.physical_exam
        .other,
    ),
  ].filter(Boolean);

  if (examination.length > 0) {
    sections.push(
      [
        "Physical examination:",
        ...examination,
      ].join("\n"),
    );
  }

  if (
    clinicalCase.laboratory_results
      .length > 0
  ) {
    sections.push(
      [
        "Laboratory results:",
        ...clinicalCase.laboratory_results.map(
          (result) => {
            const valueAndUnit = [
              result.value,
              result.unit,
            ]
              .filter(Boolean)
              .join(" ");

            const referenceRange =
              result.reference_range
                ? ` (reference: ${result.reference_range})`
                : "";

            return `- ${result.test_name}: ${valueAndUnit}${referenceRange}`;
          },
        ),
      ].join("\n"),
    );
  }

  if (
    clinicalCase.imaging.length > 0
  ) {
    sections.push(
      [
        "Imaging:",
        ...clinicalCase.imaging.flatMap(
          (study) => [
            `${study.type}:`,
            ...study.findings.map(
              (finding) =>
                `- ${finding}`,
            ),
          ],
        ),
      ].join("\n"),
    );
  }

  if (
    clinicalCase.clinical_question
      .length > 0
  ) {
    sections.push(
      formatList(
        "Clinical questions",
        clinicalCase.clinical_question,
      ),
    );
  }

  sections.push(
    [
      "Required response structure:",
      "- Most likely diagnosis",
      "- Differential diagnoses",
      "- Supporting evidence",
      "- Recommended tests",
      "- Initial management",
      "- Red flags",
      "- Confidence",
      "- Limitations",
    ].join("\n"),
  );

  return sections
    .filter(Boolean)
    .join("\n\n");
}

export async function analyzeCase(
  clinicalCase: ClinicalCase,
): Promise<StructuredAnalysisResult> {
  const request: AnalysisRequest = {
    text: formatClinicalCase(
      clinicalCase,
    ),
  };

  console.log(
    "[analyzeCase] outgoing request:",
    JSON.stringify(
      request,
      null,
      2,
    ),
  );

  const response =
    await apiRequest<unknown>(
      "/api/v1/analysis",
      {
        method: "POST",
        body: request,
        timeoutMs: 60_000,
      },
    );

  console.log(
    "[analyzeCase] raw backend response:",
    JSON.stringify(
      response,
      null,
      2,
    ),
  );

  const normalizedResult =
    normalizeStructuredResult(
      response,
    );

  console.log(
    "[analyzeCase] normalized result:",
    JSON.stringify(
      normalizedResult,
      null,
      2,
    ),
  );

  return normalizedResult;
}