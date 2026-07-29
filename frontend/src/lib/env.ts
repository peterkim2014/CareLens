const carelensApiUrl = process.env.CARELENS_API_URL;

if (!carelensApiUrl) {
  throw new Error(
    "Missing CARELENS_API_URL environment variable.",
  );
}

export const env = {
  carelensApiUrl: carelensApiUrl.replace(/\/+$/, ""),
} as const;