// Input validation for POST /api/query, using Zod (AGENTS.md / plan.md).
import { z } from "zod";
import type { QueryRequest } from "../../shared/types.js";
import { ValidationError } from "../../shared/errors.js";

const MAX_QUESTION_LEN = 1000;
const MAX_HISTORY_TURNS = 3; // ADR-0002

const historyTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1).max(MAX_QUESTION_LEN),
});

export const queryRequestSchema = z.object({
  question: z
    .string({ required_error: "question is required" })
    .trim()
    .min(1, "question must not be empty")
    .max(MAX_QUESTION_LEN, `question must be at most ${MAX_QUESTION_LEN} characters`),
  // Tier is optional on the wire; defaults to the least-privileged tier.
  tier: z.enum(["Gold", "Silver", "Standard"]).default("Standard"),
  history: z.array(historyTurnSchema).max(MAX_HISTORY_TURNS).default([]),
});

/**
 * Parses and validates an unknown request body into a QueryRequest.
 * Throws ValidationError (HTTP 400) with safe, field-level details on failure.
 */
export function parseQueryRequest(body: unknown): QueryRequest {
  const result = queryRequestSchema.safeParse(body);
  if (!result.success) {
    const details = result.error.issues.map((i) => ({
      field: i.path.join(".") || "(root)",
      message: i.message,
    }));
    throw new ValidationError("Invalid query request", details);
  }
  return result.data;
}
