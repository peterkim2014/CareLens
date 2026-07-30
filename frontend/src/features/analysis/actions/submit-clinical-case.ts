"use server";

import { analyzeCase } from "@/features/analysis/api/analyze-case";
import type {
  ClinicalCase,
  ClinicalCaseFormState,
} from "@/features/analysis/types/analysis";
import { APIError } from "@/lib/api/api-error";

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function parseClinicalCase(
  formData: FormData,
): ClinicalCase | null {
  const serializedCase =
    formData.get("clinicalCase");

  if (typeof serializedCase !== "string") {
    return null;
  }

  try {
    const parsed: unknown =
      JSON.parse(serializedCase);

    if (!isRecord(parsed)) {
      return null;
    }

    return parsed as unknown as ClinicalCase;
  } catch {
    return null;
  }
}

function validateClinicalCase(
  clinicalCase: ClinicalCase,
): string[] {
  const errors: string[] = [];

  if (
    clinicalCase.patient.age === null ||
    clinicalCase.patient.age < 0 ||
    clinicalCase.patient.age > 130
  ) {
    errors.push(
      "Enter a valid patient age.",
    );
  }

  if (
    !clinicalCase.chief_complaint.trim()
  ) {
    errors.push(
      "Enter the chief complaint.",
    );
  }

  if (
    clinicalCase.history_of_present_illness
      .symptoms.length === 0
  ) {
    errors.push(
      "Add at least one presenting symptom.",
    );
  }

  if (
    clinicalCase.clinical_question
      .filter((question) => question.trim())
      .length === 0
  ) {
    errors.push(
      "Select or enter at least one clinical question.",
    );
  }

  return errors;
}

export async function submitClinicalCase(
    _previousState: ClinicalCaseFormState,
    formData: FormData,
  ): Promise<ClinicalCaseFormState> {
    const serializedCase = formData.get(
      "clinicalCase",
    );
  
    console.log(
      "[submitClinicalCase] clinicalCase field:",
      typeof serializedCase,
      serializedCase,
    );
  
    const clinicalCase =
      parseClinicalCase(formData);
  
    console.log(
      "[submitClinicalCase] parsed case:",
      clinicalCase,
    );
  
    if (!clinicalCase) {
      return {
        status: "validation_error",
        result: null,
        message:
          "The clinical case could not be parsed.",
        traceId: null,
      };
    }
  
    const errors =
      validateClinicalCase(clinicalCase);
  
    console.log(
      "[submitClinicalCase] validation errors:",
      errors,
    );
  
    if (errors.length > 0) {
      return {
        status: "validation_error",
        result: null,
        message: errors.join(" "),
        traceId: null,
      };
    }
  
    try {
      console.log(
        "[submitClinicalCase] sending case to backend",
      );
  
      const result =
        await analyzeCase(clinicalCase);
  
      console.log(
        "[submitClinicalCase] backend result:",
        result,
      );
  
      return {
        status: "success",
        result,
        message: null,
        traceId: result.trace_id ?? null,
      };
    } catch (error) {
      console.error(
        "[submitClinicalCase] analysis failed:",
        error,
      );
  
      if (error instanceof APIError) {
        return {
          status: "error",
          result: null,
          message: error.message,
          traceId: error.traceId ?? null,
        };
      }
  
      return {
        status: "error",
        result: null,
        message:
          error instanceof Error
            ? error.message
            : "CareLens could not complete the clinical analysis.",
        traceId: null,
      };
    }
  }