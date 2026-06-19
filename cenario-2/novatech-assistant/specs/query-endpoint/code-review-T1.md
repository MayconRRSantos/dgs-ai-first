# Revisão crítica — Código da Task T1 (Dev 2.2)

> Revisão do código gerado para a 1ª task (contrato + validação). São problemas **reais** que eu
> levantaria antes de um code review/merge — não cosméticos. Cada um com ação proposta.

## 🔴 P1 — O stub 200 devolve uma "fonte" falsa e quebra o guardrail de citação

`handler.ts` retorna `200` com `source_document: { id: "PENDING", vigente: true }` e um `answer`
de placeholder. O guardrail do produto é "**toda resposta cita fonte**" — um `id: "PENDING"`
**aparenta** cumprir o contrato mas é citação inventada. Se esse stub vazar para um ambiente
integrado, o assistente responde com fonte fictícia e confiança baixa silenciosa.

**Ação:** enquanto T2..T7 não existem, o caminho de sucesso deve retornar **`501 Not Implemented`**
(ou ficar atrás de um feature flag `RAG_PIPELINE_ENABLED`), nunca um `200` com fonte falsa. O teste
AC4 deve validar o **shape** do contrato sem afirmar que é uma resposta real.

## 🟠 P2 — Validação não trata o vetor de risco de IA (prompt injection) nem orçamento de tokens

`validator.ts` limita `question` a 1000 caracteres e `history` a 3 turnos, mas:
- **Não há defesa contra prompt injection** (ex.: "ignore as instruções anteriores e..."). O QA 2.2
  lista isso como cenário de robustez obrigatório.
- O limite real do ADR-0002 é **orçamento de tokens (~8K chunks / contexto)**, não "3 turnos × 1000
  chars". 3 turnos de 1000 chars + pergunta podem extrapolar o budget na T4.

**Ação:** (a) adicionar sanitização/flagging de padrões de injection na borda (ou delegar à T4 com
nota explícita aqui); (b) trocar o limite por turno por uma estimativa de tokens agregada, alinhada
ao ADR-0002, antes de montar o prompt.

## 🟠 P3 — `AppError.details` pode vazar internals em subclasses futuras

O handler serializa `details: err.details` para qualquer `AppError`. Hoje só `ValidationError`
preenche `details` (campos seguros). Mas `InternalError` herda `details` e, se alguém anexar dados
de diagnóstico (query, stack, payload de upstream Azure), isso vai **direto para o cliente**.

**Ação:** expor `details` **apenas** para erros marcados como `clientSafe` (ex.: um getter
`exposeDetails: boolean` na classe, `true` só em `ValidationError`). Caminho 500 nunca serializa
`details`.

## 🟡 P4 (menor) — `authLevel: "function"` sem estratégia de chave/segredo definida

`authLevel: "function"` exige uma function key que ainda não tem origem definida (Key Vault? env?).
Em dev local isso passa, mas o contrato de segurança precisa ser decidido (ADR) antes do deploy.

**Ação:** registrar ADR de autenticação do endpoint; até lá, manter `function` e documentar a pendência.

---

## Resumo

| # | Severidade | Problema | Bloqueia merge? |
|---|-----------|----------|-----------------|
| P1 | 🔴 | Stub 200 com fonte falsa fere guardrail de citação | **Sim** |
| P2 | 🟠 | Sem defesa de prompt injection; budget por turno ≠ ADR-0002 | Sim (P2a) / acompanhar (P2b) |
| P3 | 🟠 | `details` pode vazar em erros 500 futuros | Sim |
| P4 | 🟡 | Auth do endpoint sem ADR | Não, mas registrar |

**Veredito:** o código compila (tsc strict), passa nos 8 testes e segue os padrões do plan
(TS/Zod/Functions v4/pino), mas **não está pronto para merge** por P1 e P3. Honestamente: o que a IA
gerou é um esqueleto correto de validação — os furos estão no que ela *aparenta* resolver (citação,
robustez de IA) mas não resolve de fato.
