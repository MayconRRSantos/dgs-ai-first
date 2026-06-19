# Estratégia de Skills — NovaTech Assistant (Dev 2.3)

> Skills são artefatos `.md` que encapsulam **como gerar** tipos específicos de output. Hierarquia
> (Anexo C): **Foundation** (convenções globais) → **Domain** (padrões por camada) → **Artifact**
> (receitas de geração). Consumidas por Copilot/Claude Code antes de gerar código/artefatos.
> Local: `/skills/foundation/`, `/skills/domain/`, `/skills/artifact/`.

## Princípio de dependência

```
Artifact  (receita: "crie um X completo")
   └─ depende de → Domain (padrão da camada)
          └─ depende de → Foundation (convenções globais)
```
Uma skill Artifact **sempre** referencia as Domain e Foundation que pressupõe. Isso evita repetir
regras e mantém uma fonte única de verdade.

## Árvore de skills

### Foundation — convenções globais (base de tudo)
| Skill | Frase-ativação (o agente reconhece) | Cria | Consome | Frequência |
|-------|--------------------------------------|------|---------|-----------|
| `typescript-conventions` | "escrever/gerar qualquer código TypeScript" | Tech Lead | Todos os devs + Copilot/Claude Code | **Altíssima** (toda geração de TS) |
| `error-handling` | "tratar erro, lançar exceção, logar, retry" | Tech Lead / Dev Sênior | Devs + agentes | Alta |
| `project-structure` | "criar arquivo/módulo novo, onde colocar" | Tech Lead | Devs + agentes | Média |

### Domain — padrões por camada
| Skill | Frase-ativação | Cria | Consome | Frequência |
|-------|----------------|------|---------|-----------|
| `azure-functions-endpoint` | "criar endpoint / HTTP trigger" | Tech Lead / Dev Sênior | Devs backend + Copilot | Alta |
| `azure-ai-search-integration` | "buscar chunks / indexar / query no AI Search" | Dev Sênior | Devs backend | Média |
| `react-components` | "criar componente/página do painel web" | Dev Front (input de Design/PS) | Devs front + Copilot | Média |
| `testing-patterns` | "escrever teste, mock, fixture" | **QA** | Devs + QA + Copilot | Alta |

### Artifact — receitas de geração completas
| Skill | Frase-ativação | Cria | Consome | Frequência | Depende de |
|-------|----------------|------|---------|-----------|-----------|
| `create-rag-endpoint` | "criar um endpoint RAG completo" | Dev Sênior | Devs + Copilot | Alta | `azure-functions-endpoint`, `azure-ai-search-integration`, Foundation |
| `create-integration-test` | "criar teste de integração para endpoint" | **QA** | Devs + QA + Copilot | Alta | `testing-patterns`, Foundation |
| `create-react-card` | "criar card de resposta/feedback no painel" | Dev Front (+ Design) | Devs front | Média | `react-components`, Foundation |
| `create-spec-sdd` *(bônus)* | "escrever requirements.md no formato SDD" | **Product Specialist** | PS + Tech Lead | Média | `project-structure` |
| `create-adr` *(bônus)* | "registrar decisão como ADR" | Tech Lead | Todos | Baixa | `project-structure` |

## Mapeamento de criação/consumo (visão de time)

A criação **não é só de devs** — cada papel é dono das skills da sua competência:

| Papel | Cria | Consome |
|-------|------|---------|
| **Tech Lead** | `typescript-conventions`, `error-handling`, `project-structure`, `azure-functions-endpoint`, `create-adr` | todas (revisão) |
| **Dev Sênior** | `azure-ai-search-integration`, `create-rag-endpoint` | Foundation + Domain |
| **Dev Pleno / Front** | `react-components`, `create-react-card` | Foundation + Domain + Artifact |
| **QA** | `testing-patterns`, `create-integration-test` | testing + Foundation |
| **Product Specialist** | `create-spec-sdd` | `project-structure` |
| **Agentes (Copilot / Claude Code)** | — (consumidores) | **todas** — leem a skill relevante antes de gerar |

## Ciclo de vida (skills são artefatos vivos)

1. **Rascunho** → autor escreve a skill.
2. **Teste real** → gera um output com o Copilot e verifica aderência (ver critérios de maturidade abaixo).
3. **Refino** → reescreve as seções que o Copilot ignorou.
4. **Madura** → critérios atendidos; entra em uso pelo time.
5. **Manutenção** → mudança de convenção/ADR dispara revisão da(s) skill(s) afetada(s).

### Critérios de "skill madura"
- O Copilot, com a skill no contexto, gera o artefato **seguindo ≥90% das regras** sem ajuste manual.
- Tem ≥1 par DO/DON'T com **código real** (não pseudocódigo).
- Lista anti-padrões observados em gerações reais (não hipotéticos).
- Referencia as skills de que depende (sem duplicar regras).

## Skill Foundation mais importante

**`typescript-conventions`** — base de todas as outras (toda geração de código TS a pressupõe).
SKILL.md completa em [`foundation/typescript-conventions.md`](./foundation/typescript-conventions.md).
