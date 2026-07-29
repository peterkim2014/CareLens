"use server";

import { analyzeQuery } from "@/features/analysis/api/analyze-query";
import type {
  AnalysisFormState,
  ClinicalQuery,
} from "@/features/analysis/types/analysis";
import { APIError } from "@/lib/api/api-error";

const MINIMUM_QUERY_LENGTH = 10;
const MAXIMUM_QUERY_LENGTH = 4_000;

function readQuery(formData: FormData): string {
  const value = formData.get("query");

  return typeof value === "string"
    ? value.trim()
    : "";
}

function validateQuery(
  query: string,
): string[] {
  const errors: string[] = [];

  if (!query) {
    errors.push(
      "Enter a clinical question or scenario.",
    );

    return errors;
  }

  if (query.length < MINIMUM_QUERY_LENGTH) {
    errors.push(
      `The query must contain at least ${MINIMUM_QUERY_LENGTH} characters.`,
    );
  }

  if (query.length > MAXIMUM_QUERY_LENGTH) {
    errors.push(
      `The query must contain no more than ${MAXIMUM_QUERY_LENGTH} characters.`,
    );
  }

  return errors;
}

export async function submitAnalysis(
  _previousState: AnalysisFormState,
  formData: FormData,
): Promise<AnalysisFormState> {
  const query = readQuery(formData);
  const queryErrors = validateQuery(query);

  if (queryErrors.length > 0) {
    return {
      status: "validation_error",
      values: {
        query,
      },
      errors: {
        query: queryErrors,
      },
      result: null,
      message:
        "Review the highlighted field and submit again.",
      traceId: null,
    };
  }

  const request: ClinicalQuery = {
    query,
  };

  try {
    const result = await analyzeQuery(request);

    return {
      status: "success",
      values: {
        query,
      },
      errors: {},
      result,
      message: null,
      traceId: result.trace_id ?? null,
    };
  } catch (error) {
    if (error instanceof APIError) {
      return {
        status: "error",
        values: {
          query,
        },
        errors: {},
        result: null,
        message: error.message,
        traceId: error.traceId ?? null,
      };
    }

    return {
      status: "error",
      values: {
        query,
      },
      errors: {},
      result: null,
      message:
        "CareLens could not complete the analysis.",
      traceId: null,
    };
  }
}