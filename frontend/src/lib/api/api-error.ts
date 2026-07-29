export interface APIErrorDetails {
    code?: string;
    message?: string;
    trace_id?: string;
    details?: unknown;
  }
  
  export interface APIErrorResponse {
    error?: APIErrorDetails;
  }
  
  export class APIError extends Error {
    readonly status: number;
    readonly code: string | undefined;
    readonly traceId: string | undefined;
    readonly details: unknown;
  
    constructor({
      status,
      message,
      code,
      traceId,
      details,
    }: {
      status: number;
      message: string;
      code?: string;
      traceId?: string;
      details?: unknown;
    }) {
      super(message);
  
      this.name = "APIError";
      this.status = status;
      this.code = code;
      this.traceId = traceId;
      this.details = details;
    }
  }