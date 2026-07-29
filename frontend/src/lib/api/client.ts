import { env } from "@/lib/env";

import {
  APIError,
  type APIErrorResponse,
} from "./api-error";

type SerializableRequestBody = object;

type RequestBody =
  | BodyInit
  | SerializableRequestBody;

export interface APIRequestOptions
  extends Omit<RequestInit, "body" | "signal"> {
  body?: RequestBody;
  timeoutMs?: number;
  signal?: AbortSignal;
}

function isNativeBody(
  body: RequestBody,
): body is BodyInit {
  return (
    typeof body === "string" ||
    body instanceof Blob ||
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof ArrayBuffer ||
    ArrayBuffer.isView(body) ||
    body instanceof ReadableStream
  );
}

function prepareRequestBody(
  body: RequestBody | undefined,
  headers: Headers,
): BodyInit | undefined {
  if (body === undefined) {
    return undefined;
  }

  if (isNativeBody(body)) {
    return body;
  }

  if (!headers.has("Content-Type")) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  return JSON.stringify(body);
}

async function parseResponseBody(
  response: Response,
): Promise<unknown> {
  if (
    response.status === 204 ||
    response.status === 205
  ) {
    return null;
  }

  const contentType =
    response.headers.get("content-type") ?? "";

  if (
    contentType.includes("application/json") ||
    contentType.includes("+json")
  ) {
    return response.json();
  }

  return response.text();
}

function isAPIErrorResponse(
  value: unknown,
): value is APIErrorResponse {
  if (
    typeof value !== "object" ||
    value === null
  ) {
    return false;
  }

  const candidate =
    value as Record<string, unknown>;

  return (
    candidate.error === undefined ||
    (typeof candidate.error === "object" &&
      candidate.error !== null)
  );
}

function createAPIError(
  response: Response,
  responseBody: unknown,
): APIError {
  const errorResponse = isAPIErrorResponse(
    responseBody,
  )
    ? responseBody
    : null;

  return new APIError({
    status: response.status,
    message:
      errorResponse?.error?.message ||
      response.statusText ||
      "The API request failed.",
    code: errorResponse?.error?.code,
    traceId:
      errorResponse?.error?.trace_id ??
      response.headers.get("X-Trace-ID") ??
      undefined,
    details: errorResponse?.error?.details,
  });
}

function combineAbortSignals(
  timeoutSignal: AbortSignal,
  externalSignal?: AbortSignal,
): AbortSignal {
  if (!externalSignal) {
    return timeoutSignal;
  }

  return AbortSignal.any([
    timeoutSignal,
    externalSignal,
  ]);
}

export async function apiRequest<T>(
  path: string,
  options: APIRequestOptions = {},
): Promise<T> {
  const {
    body,
    headers,
    timeoutMs = 10_000,
    signal,
    ...requestOptions
  } = options;

  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Accept")) {
    requestHeaders.set(
      "Accept",
      "application/json",
    );
  }

  const requestBody = prepareRequestBody(
    body,
    requestHeaders,
  );

  const timeoutController =
    new AbortController();

  const timeout = setTimeout(
    () => timeoutController.abort(),
    timeoutMs,
  );

  const requestSignal = combineAbortSignals(
    timeoutController.signal,
    signal,
  );

  try {
    const response = await fetch(
      `${env.carelensApiUrl}${path}`,
      {
        ...requestOptions,
        body: requestBody,
        headers: requestHeaders,
        signal: requestSignal,
        cache: "no-store",
      },
    );

    const responseBody =
      await parseResponseBody(response);

    if (!response.ok) {
      throw createAPIError(
        response,
        responseBody,
      );
    }

    return responseBody as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw new APIError({
        status: 504,
        code: "api_timeout",
        message:
          "The CareLens API did not respond in time.",
      });
    }

    throw new APIError({
      status: 503,
      code: "api_unavailable",
      message:
        "The CareLens API is currently unavailable.",
      details:
        error instanceof Error
          ? error.message
          : undefined,
    });
  } finally {
    clearTimeout(timeout);
  }
}