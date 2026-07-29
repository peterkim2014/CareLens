import "server-only";

import { apiRequest } from "@/lib/api/client";

import type {
  AnalysisResult,
  ClinicalQuery,
} from "../types/analysis";

export async function analyzeQuery(
  query: ClinicalQuery,
): Promise<AnalysisResult> {
  return apiRequest<AnalysisResult>(
    "/api/v1/analysis",
    {
      method: "POST",
      body: query,
      timeoutMs: 30_000,
    },
  );
}