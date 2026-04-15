export interface ResultEnvelope {
  protocol: "aclip/0.1";
  type: "result";
  ok: true;
  command: string;
  data: Record<string, unknown>;
}

export const AUTH_ERROR_CODES = [
  "auth_required",
  "invalid_credential",
  "expired_credential"
] as const;

export interface ErrorEnvelope {
  protocol: "aclip/0.1";
  type: "error";
  ok: false;
  command: string;
  error: {
    code: string;
    message: string;
  };
}

export function encodeJson(payload: unknown): string {
  return `${JSON.stringify(payload)}\n`;
}

export function resultEnvelope(command: string, data: unknown): ResultEnvelope {
  return {
    protocol: "aclip/0.1",
    type: "result",
    ok: true,
    command,
    data: isRecord(data) ? data : { result: data }
  };
}

export function errorEnvelope(command: string, code: string, message: string): ErrorEnvelope {
  return {
    protocol: "aclip/0.1",
    type: "error",
    ok: false,
    command,
    error: {
      code,
      message
    }
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
