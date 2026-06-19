# MCP Servers — Mapeamento de Necessidades (Dev 2.1)

> Mapeia cada necessidade do projeto NovaTech Assistant a um **reference server local e
> gratuito** (`filesystem`, `git`, `memory`, `everything`). Nenhum serviço pago/externo.
> Config final: [`.mcp/mcp.json`](../../.mcp/mcp.json). Evidência de execução:
> [`mcp-evidence.md`](./mcp-evidence.md). Riscos: [`mcp-security-risks.md`](./mcp-security-risks.md).

## 1. Necessidade → Server → Escopo

| # | Necessidade do projeto | Server | Primitivas MCP expostas | Quem consome | Escopo concedido | Modo |
|---|------------------------|--------|--------------------------|--------------|------------------|------|
| 1 | Ler/editar código, specs e skills | `filesystem` | **Tools**: `read_text_file`, `read_multiple_files`, `list_directory`, `directory_tree`, `search_files`, `write_file`, `edit_file`, `create_directory`, `move_file`, `get_file_info` | Claude Code, Copilot (devs, Tech Lead) | `./src ./specs ./skills ./prompts` | leitura+escrita |
| 2 | Ler documentação de negócio (era Confluence) | `filesystem` | mesmas tools (usadas só p/ leitura) | Agentes ao gerar respostas/guardrails | `./docs` (inclui `docs/novatech/`) | **read-only por política** |
| 3 | "Recuperar" chunks (era Azure AI Search) | `filesystem` | `read_text_file`, `search_files` | Agente de RAG / testes | `./data` (inclui `data/retrieval-corpus/`) | **read-only por política** |
| 4 | Histórico, diff e branches do repo (era GitHub) | `git` | **Tools**: `git_log`, `git_status`, `git_diff`, `git_diff_staged`, `git_diff_unstaged`, `git_show`, `git_branch`, `git_create_branch`, `git_checkout`, `git_add`, `git_commit`, `git_reset` | Agentes (auditoria, contexto de mudanças) | `--repository .` | leitura (escrita via `git_commit` evitada) |
| 5 | Glossário/linguagem ubíqua + decisões persistentes | `memory` | **Tools**: knowledge graph (`create_entities`, `create_relations`, `add_observations`, `search_nodes`, `read_graph`) | Todos os agentes (memória entre sessões) | grafo local em arquivo | leitura+escrita |
| (extra) | Aprender as primitivas MCP (tools/resources/prompts) | `everything` | **Tools + Resources + Prompts** (servidor de referência) | Time (aprendizado) | — | sandbox |

> Confirmação de primitivas: os nomes acima foram obtidos via `tools/list` real contra os
> servers (ver `mcp-evidence.md`) — não são suposições. O `filesystem` v0.2.0 expôs 14 tools;
> o `git` v1.28.0 expôs 12 tools.

## 2. Por que `filesystem`, `git`, `memory`, `everything` (e não os da nuvem)

| Antes (cenário real) | Agora (fase de estruturação, local) | Server |
|----------------------|-------------------------------------|--------|
| Confluence | `docs/novatech/` (Anexo A) | `filesystem` |
| Azure AI Search | `data/retrieval-corpus/` (Anexo B) | `filesystem` |
| GitHub | repositório git local | `git` |
| Banco de decisões/glossário | grafo de memória local | `memory` |

O server de GitHub do upstream foi **arquivado** e exigiria conta/token externos — por isso o
repositório é tratado localmente com `filesystem` + `git`.

## 3. Least privilege — justificativa por server

### `filesystem` — escopo mínimo, fontes de negócio read-only
- **Não recebe a raiz `.`** — isso exporia `.env`, `.git/`, `infra/parameters/*.bicepparam`
  (segredos) e permitiria escrita irrestrita. Recebe **apenas** as 6 pastas de trabalho.
- **rw** em `./src ./specs ./skills ./prompts` — são os artefatos que os agentes produzem.
- **read-only** em `./docs` e `./data` — são **fontes de verdade**. O reference filesystem
  server **não tem flag read-only nativa por raiz**; portanto o read-only é garantido por:
  1. **Política** (este documento + AGENTS.md): agentes não escrevem em `docs/novatech/` nem
     `data/retrieval-corpus/`.
  2. **Auditoria** via `git` MCP: qualquer escrita aparece no `git diff`/`git status` e é
     barrada no validation gate de code review.
  3. **Reforço opcional**: rodar uma 2ª instância do `filesystem` server só com `./docs ./data`
     em um agente "leitor", ou marcar as pastas read-only no SO/ACL.
  > Esta limitação do reference server é, ela própria, um dos riscos documentados em
  > `mcp-security-risks.md` (R2).

### `git` — leitura de histórico
- Escopo `--repository .`: o server enxerga só este repositório.
- O time **evita** expor/usar `git_commit`/`git_reset` por agente sem gate — commits são feitos
  por humano ou após validation gate (ver contingência em `mcp-security-risks.md`).

### `memory` — grafo local
- Persiste só o que o time grava (glossário, decisões). Não acessa o filesystem do projeto.

### `everything` — sandbox de aprendizado
- Sem acesso a dados do projeto; serve para inspecionar as 3 primitivas MCP.

## 4. Pré-requisitos de ambiente

- **node + npx** (≥ v18) — para `filesystem`, `memory`, `everything`.
- **uv/uvx** — para `git` (`uvx mcp-server-git`). Instalar com `pip install uv` (feito nesta
  máquina: `uv 0.11.22`) ou via installer oficial; garantir `uvx` no `PATH`.
- Os comandos/pacotes evoluem — confirmar no README oficial `modelcontextprotocol/servers`.
