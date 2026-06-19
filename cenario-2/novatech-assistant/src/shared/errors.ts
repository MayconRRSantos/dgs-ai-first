// Custom errors. Every error carries an HTTP status so the handler can map it
// without leaking stack traces to the client.

export abstract class AppError extends Error {
  abstract readonly statusCode: number;
  /** Safe, client-facing details (must not contain secrets or stack traces). */
  readonly details?: unknown;

  constructor(message: string, details?: unknown) {
    super(message);
    this.name = new.target.name;
    this.details = details;
  }
}

/** Input failed validation. Maps to HTTP 400. */
export class ValidationError extends AppError {
  readonly statusCode = 400;
}

/** Unexpected downstream/internal failure. Maps to HTTP 500. */
export class InternalError extends AppError {
  readonly statusCode = 500;
}
