# Avaliação do Exercício 2.2 — Desenvolvedor (SDD: plan → tasks → código)

> Autoavaliação seguindo `avaliacao-foundation.md` + `avaliacao-desenvolvedor.md`.

### Resumo

Decomposição do `plan.md` em 7 tasks atômicas com critérios de aceite verificáveis; 1ª task
(contrato + validação Zod) implementada nos padrões do plan (TS strict, Functions v4, pino),
**compilando** (`tsc --noEmit` OK) e com **8 testes verdes** cobrindo AC1–AC5. Revisão crítica
aponta 4 problemas reais (não cosméticos), incluindo o furo do stub que finge citar fonte.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | **3** | SDD aplicado de verdade: plan→tasks atômicas com ID, deps, AC e estimativa P/M/G; cada task implementável/testável isolada. |
| D2 — Uso de Ferramentas | **3** | Evidência de execução real: `tsc --noEmit` (strict) OK e `vitest run` com 8/8 verdes (log estruturado pino visível). Geração + verificação + revisão crítica documentadas. |
| D3 — Qualidade do Entregável | **3** | `tasks.md` completo e acionável; código nos paths do Anexo C (`src/functions/query/`, `src/shared/`), Zod, sem `console.log`; AC verificáveis ("400 para body sem question"). |
| D4 — Pensamento Crítico | **3** | Revisão crítica com 4 problemas **reais** (stub com fonte falsa fere guardrail; sem defesa de prompt injection; budget por turno ≠ ADR-0002; vazamento de `details` em 500). Veredito honesto "não pronto para merge". |
| D5 — Aplicabilidade ao Projeto | **3** | Referencia ADR-0002 (budget), ADR-0003 (vigência), protótipo open-source do cenário 1 (Dev 1.3), linguagem ubíqua (tier ≠ metal, "Platinum" inexistente) e guardrail de citação. |

**Score do exercício: 3.0**

### Checklist do papel (Dev 2.2)

- ✅ Tasks atômicas (T1..T7, deps explícitas)
- ✅ Critérios de aceite verificáveis (HTTP 400/200, limites)
- ✅ Código segue padrões do plan (TS/Zod/Functions v4/pino)
- ✅ Código segue Anexo C (paths corretos)
- ✅ Revisão crítica real (4 problemas, não inventados)
- ✅ Conecta com cenário 1 (Dev 1.3, ADR-0002/0003)

### Pontos Fortes

1. Testes reais verdes provam os critérios de aceite (não é "deve funcionar").
2. Revisão crítica encontra o furo sutil: o stub *aparenta* citar fonte (`id:"PENDING"`) e fere o guardrail — exatamente o tipo de erro que passa despercebido.

### Pontos de Melhoria

1. Os fixes propostos na revisão (501 em vez de 200-stub, `exposeDetails`) ficaram como proposta — aplicá-los seria um "v2" demonstrável.
2. Ferramenta nominal: implementado como agente (Claude Code) com verificação real, não via UI do Copilot — anexar print do Copilot se a ferramenta nominal for exigida.

### Classificação

**Aprovado com distinção (3.0)**
