# Avaliação do Exercício 2.3 — Desenvolvedor (estratégia de skills)

> Autoavaliação seguindo `avaliacao-foundation.md` + `avaliacao-desenvolvedor.md`.

### Resumo

Árvore de skills coerente (Foundation→Domain→Artifact) mapeada a artefatos realmente repetidos no
projeto, com criação/consumo **multi-papel** (QA cria testing, PS cria spec). A SKILL.md Foundation
(`typescript-conventions`) é prescritiva, com DO/DON'T em código real do domínio e anti-padrões que
o Copilot gera de fato — e foi **verificada** contra o código de 2.2 (tsc strict OK, sem anti-padrões).

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | **3** | Hierarquia Foundation→Domain→Artifact aplicada com regra de dependência explícita (Artifact→Domain→Foundation); distingue convenção global × padrão de camada × receita. |
| D2 — Uso de Ferramentas | **3** | A SKILL.md não é teórica: seu comando de verificação (`tsc --noEmit` + grep de anti-padrões) foi **executado** contra `src/` e confirma aderência (único hit é um comentário). |
| D3 — Qualidade do Entregável | **3** | `SKILLS-STRATEGY.md` completo e acionável; SKILL.md com frontmatter machine-readable (`name/activation/owner/consumers/depends_on`), DO/DON'T em TS real, tabela de anti-padrões. Paths do Anexo C. |
| D4 — Pensamento Crítico | **3** | Anti-padrões são reais (`as any`, `console.log`, `tier: string` → "Platinum", import sem `.js`, `export default`), com o porquê e a correção; critérios de "skill madura" mensuráveis. |
| D5 — Aplicabilidade ao Projeto | **3** | Skills mapeiam artefatos do NovaTech (RAG endpoint, integration test, react card); reusa `src/shared`/`validator.ts` de 2.2; linguagem ubíqua (tier ≠ metal); respeita `/skills/{foundation,domain,artifact}`. |

**Score do exercício: 3.0**

### Verificação Machine-Readable

- Frontmatter YAML parseável (`name`, `activation`, `owner`, `consumers`, `depends_on`). ✅
- Regras em formato DEVE/NÃO DEVE; exemplos em blocos de código tipados; tabela de anti-padrões. ✅
- Nada narrativo-demais: cada regra é uma instrução acionável.

### Checklist do papel (Dev 2.3)

- ✅ Árvore coerente com o projeto (sem skills teóricas)
- ✅ Criação/consumo multi-papel (QA, PS, TL, Devs, agentes)
- ✅ SKILL.md Foundation concreto (código TS real DO/DON'T)
- ✅ Anti-padrões úteis (`as any`, `console.log`, require dinâmico, tier frouxo)
- ✅ Referencia Anexo C (hierarquia de diretórios)

### Pontos de Melhoria

1. As SKILL.md Domain/Artifact ficaram como árvore mapeada (não escritas) — escopo correto do exercício, mas escrever `azure-functions-endpoint` seria o próximo passo (é o exercício do Tech Lead 2.3).
2. Teste de aderência feito via verificação determinística; um teste gerando código novo com o Copilot e medindo % de regras seguidas seria evidência ainda mais forte.

### Classificação

**Aprovado com distinção (3.0)**
