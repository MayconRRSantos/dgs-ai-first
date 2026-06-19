# Tasks — Query Endpoint

> Gerado pelo Dev (Dev 2.2) a partir do `plan.md`, com apoio de IA. Aprovação: Tech Lead (Gate 2).
> Cada task é atômica: implementável e testável isoladamente. Estimativa: P (≤2h) / M (≤1d) / G (>1d).

## Legenda de dependências

`T1` → contrato/validação é base de quase tudo. Tasks sem Azure são testáveis com mocks (msw).

---

### T1 — Contrato da API + validação de input  `[P]`  ✅ IMPLEMENTADA (Dev 2.2)

- **Descrição:** Definir tipos do domínio (`QueryRequest`, `QueryResponse` com `source_document`),
  schema Zod de input, e o HTTP trigger `POST /api/query` (Azure Functions v4) que valida o body
  e responde com o contrato. Sem dependência de Azure — retorna 200 com stub do contrato.
- **Critérios de aceite (verificáveis):**
  - AC1: `POST /api/query` com body `{ "question": "" }` (vazio) ou sem `question` → **HTTP 400** com JSON `{ error, details }`.
  - AC2: `question` com >1000 chars → **HTTP 400** (limite de input).
  - AC3: `tier` ausente é aceito (default `Standard`); `tier` inválido (≠ Gold/Silver/Standard) → **400**.
  - AC4: body válido → **HTTP 200** com JSON contendo os campos `answer`, `source_document`, `confidence`.
  - AC5: `tsc --noEmit` passa em strict; nenhum `console.log` (usa `logger` pino).
- **Dependências:** nenhuma.
- **Estimativa:** P.

### T2 — Search service (Azure AI Search, top-5 chunks)  `[M]`

- **Descrição:** `src/services/search.ts` — consulta o índice e retorna top-5 chunks com metadado de vigência.
- **Critérios de aceite:** AC1: retorna ≤5 chunks ordenados por score; AC2: cada chunk tem `id`, `content`, `source_document`, `vigente:boolean`; AC3: testado com mock msw (sem Azure real).
- **Dependências:** T1 (tipos). **Estimativa:** M.

### T3 — Embedding service (Azure OpenAI)  `[P]`

- **Descrição:** `src/services/completion.ts` (parte embedding) — gera embedding da pergunta.
- **Critérios de aceite:** AC1: retorna vetor `number[]`; AC2: erro de API → lança `AppError` (não vaza stack ao cliente).
- **Dependências:** nenhuma (paralela a T2). **Estimativa:** P.

### T4 — Prompt builder com context budget (ADR-0002)  `[M]`

- **Descrição:** `src/services/prompt-builder.ts` — monta prompt = system (~4K) + ≤5 chunks (~8K) + pergunta + histórico (3 turnos).
- **Critérios de aceite:** AC1: trunca/seleciona chunks p/ respeitar ~8K tokens; AC2: prioriza chunk `vigente` (ADR-0003); AC3: nunca excede o budget total.
- **Dependências:** T1. **Estimativa:** M.

### T5 — Completion service GPT-4o + retry/backoff  `[M]`

- **Descrição:** chamada ao GPT-4o com retry exponencial.
- **Critérios de aceite:** AC1: 3 tentativas com backoff; AC2: timeout → `AppError`; AC3: testado com mock.
- **Dependências:** T3. **Estimativa:** M.

### T6 — Response builder com `source_document` (ADR-0003)  `[P]`

- **Descrição:** `src/functions/query/response-builder.ts` — monta `QueryResponse` citando fonte; se 2 versões, marca vigente e informa anterior.
- **Critérios de aceite:** AC1: `source_document` sempre presente; AC2: confiança baixa → flag `low_confidence`; AC3: contradição → cita versão vigente + nota.
- **Dependências:** T1, T2, T5. **Estimativa:** P.

### T7 — Wiring do handler (orquestração)  `[M]`

- **Descrição:** handler chama T2→T4→T5→T6 e retorna 200.
- **Critérios de aceite:** AC1: e2e com mocks retorna resposta com fonte em <30s (VC-01); AC2: pergunta sem match → mensagem padrão "não encontrado" (não inventa).
- **Dependências:** T2, T4, T5, T6. **Estimativa:** M.

---

## Ordem sugerida

T1 → (T2 ‖ T3) → (T4 ‖ T5) → T6 → T7. T1 implementada neste exercício; demais são o roadmap do módulo.
