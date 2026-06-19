// HTTP trigger for the query endpoint (Azure Functions v4).
// Dev 2.2 / Task T1: contract + input validation. The RAG pipeline (search -> prompt ->
// completion -> response) lands in T2..T7; here we validate and return the response contract.
import { app, type HttpRequest, type HttpResponseInit, type InvocationContext } from "@azure/functions";
import { parseQueryRequest } from "./validator.js";
import { AppError } from "../../shared/errors.js";
import { logger } from "../../shared/logger.js";
import type { QueryResponse } from "../../shared/types.js";

export async function queryHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "Invalid JSON body" });
  }

  try {
    const query = parseQueryRequest(body);
    logger.info({ invocationId: context.invocationId, tier: query.tier }, "query received");

    // TODO(T2..T7): search top-5 chunks -> build prompt (budget ADR-0002) -> GPT-4o
    // -> response with real source_document (ADR-0003). Stub keeps the contract testable.
    const response: QueryResponse = {
      answer: "[stub] resposta será gerada pelo pipeline de RAG (T2..T7).",
      source_document: { id: "PENDING", vigente: true },
      confidence: "low",
      low_confidence: true,
    };
    return json(200, response);
  } catch (err) {
    if (err instanceof AppError) {
      return json(err.statusCode, { error: err.message, details: err.details });
    }
    logger.error({ err }, "unexpected error in queryHandler");
    return json(500, { error: "Internal server error" });
  }
}

function json(status: number, payload: unknown): HttpResponseInit {
  return { status, jsonBody: payload };
}

app.http("query", {
  methods: ["POST"],
  authLevel: "function",
  route: "query",
  handler: queryHandler,
});
