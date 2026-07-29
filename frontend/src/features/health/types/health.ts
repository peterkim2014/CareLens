export type SemanticRetrievalStatus =
  | "disabled"
  | "available"
  | "cooldown"
  | "unavailable";

export interface HealthResponse {
  status: "healthy";
  service: string;
  version: string;
  environment: string;

  semantic_retrieval_enabled: boolean;
  semantic_retrieval_status:
    SemanticRetrievalStatus;
  semantic_retrieval_error: string | null;
  semantic_last_failure_at: string | null;
  semantic_last_recovery_attempt_at:
    | string
    | null;
  semantic_recovery_cooldown_seconds: number;
}