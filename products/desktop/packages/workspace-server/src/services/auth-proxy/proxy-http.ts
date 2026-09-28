import type http from "node:http";

export const STRIPPED_REQUEST_HEADERS = new Set([
  "authorization",
  "x-api-key",
  "api-key",
  "anthropic-auth-token",
  "proxy-authorization",
  "content-length",
  "transfer-encoding",
]);

export const STRIPPED_RESPONSE_HEADERS = new Set([
  "transfer-encoding",
  "content-encoding",
  "content-length",
]);

export function jsonError(
  res: http.ServerResponse,
  status: number,
  error: Record<string, string>,
  extraHeaders: Record<string, string> = {},
): void {
  if (res.headersSent) {
    res.end();
    return;
  }
  res.writeHead(status, {
    "content-type": "application/json",
    ...extraHeaders,
  });
  res.end(JSON.stringify({ error }));
}

export function responseHeaders(
  response: Response,
  stripped: ReadonlySet<string>,
): Record<string, string> {
  const headers: Record<string, string> = {};
  response.headers.forEach((value: string, key: string) => {
    if (stripped.has(key.toLowerCase())) return;
    headers[key] = value;
  });
  return headers;
}
