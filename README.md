# Trilha de Certificação AI First — Engenharia de Software Agêntica

Repositório de exercícios práticos da **Trilha AI First** da DB1 Global Software (Maio/2026).

## Estrutura

| Cenário                 | Tema                            | Status       |
| ----------------------- | ------------------------------- | ------------ |
| [cenario-1](cenario-1/) | Fase de Entendimento e Contexto    | ✅ Concluído |
| [cenario-2](cenario-2/) | Fase de Estruturação do Trabalho   | ✅ Concluído |
| cenario-3               | _(próximo)_                        | 🔲 Pendente  |

## Blocos de Conhecimento Cobertos

1. Fundamentos de IA Generativa
2. Engenharia de Prompt
3. Engenharia de Contexto
4. RAG e MCP
5. AI Agents
6. Recorte de Domínio e Spec Driven Development
7. AGENTS.md
8. Skills
9. Harness Engineering: HITL e Structured Outputs
10. Revisão Crítica de Outputs de IA

## Cenário 1 — Fase de Entendimento e Contexto

**Tópicos:** Fundamentos de IA Generativa, Engenharia de Prompt, Engenharia de Contexto, RAG

**Papel exercido:** Desenvolvedor

### Exercícios entregues

| Exercício | Descrição                                                                      | Pasta                      |
| --------- | ------------------------------------------------------------------------------ | -------------------------- |
| 1.1       | Análise de viabilidade técnica com fundamentos de LLM e engenharia de contexto | `cenario-1/exercicio-1.1/` |
| 1.2       | Prototipação de prompt com engenharia de contexto                              | `cenario-1/exercicio-1.2/` |
| 1.3       | Construção de pipeline de RAG com ferramentas open-source                      | `cenario-1/exercicio-1.3/` |

### Stack utilizada (Exercício 1.3)

- Python 3.12
- ChromaDB (vector store local)
- sentence-transformers (`all-MiniLM-L6-v2`)
- Claude (geração via chat)

## Cenário 2 — Fase de Estruturação do Trabalho

**Tópicos:** MCP, Recorte de Domínio e Spec Driven Development, AGENTS.md, Skills

**Papel exercido:** Desenvolvedor

O cenário usa o repositório de trabalho `cenario-2/novatech-assistant/` (Anexo D — starter repo
Git local), onde vivem os entregáveis de código e configuração.

### Exercícios entregues

| Exercício | Descrição                                          | Entregáveis (em `cenario-2/novatech-assistant/`)                                  |
| --------- | -------------------------------------------------- | --------------------------------------------------------------------------------- |
| 2.1       | Configuração e uso real de MCP servers locais      | `.mcp/mcp.json`, `docs/mcp/` (mapeamento, evidência de execução real, riscos)      |
| 2.2       | Implementação de spec com SDD (query endpoint)     | `specs/query-endpoint/` (tasks + revisão), `src/functions/query/`, `src/shared/`, testes |
| 2.3       | Estratégia de skills do projeto                    | `skills/SKILLS-STRATEGY.md`, `skills/foundation/typescript-conventions.md`         |

Autoavaliações pela rubrica oficial em `cenario-2/autoavaliacao/` — **todas 3.0 (Aprovado com distinção)**.

### Stack utilizada (Cenário 2)

- TypeScript (strict), Azure Functions v4, Zod, pino, Vitest
- MCP servers locais: `filesystem`, `git`, `memory`, `everything` (via `npx`/`uvx`)

## Ferramentas utilizadas

- **GitHub Copilot** — assistência na codificação e iteração de prompts
- **Claude** (chat) — análise, revisão crítica e geração de respostas

## Como executar o pipeline RAG (Cenário 1.3)

```bash
cd cenario-1/exercicio-1.3
pip install -r requirements.txt
python ingest.py          # indexa documentos no ChromaDB
python run_tests.py       # executa testes de retrieval
```

## Autor

Maycon Santos — DB1 Global Software
