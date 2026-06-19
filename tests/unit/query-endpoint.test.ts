// Verifies the acceptance criteria of Task T1 (Dev 2.2): contract + input validation.
import { describe, it, expect } from "vitest";
import { parseQueryRequest } from "../../src/functions/query/validator.js";
import { queryHandler } from "../../src/functions/query/handler.js";
import { ValidationError } from "../../src/shared/errors.js";
import type { HttpRequest, InvocationContext } from "@azure/functions";

function mockRequest(body: unknown): HttpRequest {
  return { json: async () => body } as unknown as HttpRequest;
}
const ctx = { invocationId: "test-123" } as unknown as InvocationContext;

describe("parseQueryRequest (validator)", () => {
  it("should throw ValidationError when question is missing (AC1)", () => {
    expect(() => parseQueryRequest({})).toThrow(ValidationError);
  });

  it("should throw ValidationError when question is empty (AC1)", () => {
    expect(() => parseQueryRequest({ question: "   " })).toThrow(ValidationError);
  });

  it("should throw ValidationError when question exceeds 1000 chars (AC2)", () => {
    expect(() => parseQueryRequest({ question: "a".repeat(1001) })).toThrow(ValidationError);
  });

  it("should default tier to Standard when absent (AC3)", () => {
    expect(parseQueryRequest({ question: "Qual o SLA Gold?" }).tier).toBe("Standard");
  });

  it("should throw ValidationError for an invalid tier like Platinum (AC3)", () => {
    expect(() => parseQueryRequest({ question: "ok", tier: "Platinum" })).toThrow(ValidationError);
  });
});

describe("queryHandler (HTTP contract)", () => {
  it("should return 400 with details for an invalid body (AC1)", async () => {
    const res = await queryHandler(mockRequest({ question: "" }), ctx);
    expect(res.status).toBe(400);
    expect((res.jsonBody as { details: unknown }).details).toBeTruthy();
  });

  it("should return 200 with the response contract for a valid body (AC4)", async () => {
    const res = await queryHandler(mockRequest({ question: "Qual o prazo de devolução?" }), ctx);
    expect(res.status).toBe(200);
    const body = res.jsonBody as Record<string, unknown>;
    expect(body).toHaveProperty("answer");
    expect(body).toHaveProperty("source_document");
    expect(body).toHaveProperty("confidence");
  });

  it("should return 400 when the body is not valid JSON (edge case)", async () => {
    const bad = { json: async () => { throw new Error("bad json"); } } as unknown as HttpRequest;
    const res = await queryHandler(bad, ctx);
    expect(res.status).toBe(400);
  });
});
