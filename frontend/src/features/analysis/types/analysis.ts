export interface ClinicalQuery {
  query: string;
}

export type RiskLevel =
  | "low"
  | "moderate"
  | "high"
  | "emergency";

export interface RiskAssessment {
  risk_level: RiskLevel;
  rationale: string;
}

export interface AnalysisResult {
  risk_assessment: RiskAssessment;
  response: string;
  trace_id?: string;
}

export interface AnalysisFormValues {
  query: string;
}

export type AnalysisFormErrors = Partial<
  Record<keyof AnalysisFormValues, string[]>
>;

export type AnalysisFormState =
  | {
      status: "idle";
      values: AnalysisFormValues;
      errors: AnalysisFormErrors;
      result: null;
      message: null;
      traceId: null;
    }
  | {
      status: "validation_error";
      values: AnalysisFormValues;
      errors: AnalysisFormErrors;
      result: null;
      message: string;
      traceId: null;
    }
  | {
      status: "success";
      values: AnalysisFormValues;
      errors: AnalysisFormErrors;
      result: AnalysisResult;
      message: null;
      traceId: string | null;
    }
  | {
      status: "error";
      values: AnalysisFormValues;
      errors: AnalysisFormErrors;
      result: null;
      message: string;
      traceId: string | null;
    };

export const initialAnalysisFormState: AnalysisFormState = {
  status: "idle",
  values: {
    query: "",
  },
  errors: {},
  result: null,
  message: null,
  traceId: null,
};