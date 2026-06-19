// Domain types for the NovaTech Assistant query endpoint.
// Ubiquitous language (see AGENTS.md / Anexo A): "tier" is a customer tier, not a metal.

/** Customer tiers. NovaTech has exactly three (SLA-2024). No "Platinum". */
export type Tier = "Gold" | "Silver" | "Standard";

/** A turn of conversation history. Limited to 3 turns by ADR-0002. */
export interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
}

/** Validated input of POST /api/query. */
export interface QueryRequest {
  question: string;
  tier: Tier;
  history: HistoryTurn[];
}

/** Citation of the source backing an answer (ADR-0003: vigência). */
export interface SourceDocument {
  /** Document identifier, e.g. "SLA-2024" or "PROC-042-v2". */
  id: string;
  /** Section reference inside the document, when known. */
  section?: string;
  /** Whether this is the current (vigente) version when versions conflict. */
  vigente: boolean;
}

export type Confidence = "high" | "medium" | "low";

/** Response contract. `source_document` is ALWAYS present (guardrail). */
export interface QueryResponse {
  answer: string;
  source_document: SourceDocument;
  confidence: Confidence;
  /** Set when confidence is low — UI prefixes a warning and suggests escalation. */
  low_confidence: boolean;
}
