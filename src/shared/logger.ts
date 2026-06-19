// Structured logger (pino). NEVER use console.log in this project (AGENTS.md).
import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  // Redact common secret-bearing fields so they never reach the logs.
  redact: ["req.headers.authorization", "*.apiKey", "*.connectionString"],
});

export type Logger = typeof logger;
