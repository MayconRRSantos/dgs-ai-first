# MCP Servers — Análise de Riscos de Segurança (Dev 2.1)

> Riscos **específicos deste setup local** (servers MCP rodando via `npx`/`uvx` na máquina do
> dev, com acesso ao repositório `novatech-assistant`) e mitigações **acionáveis**. Não são
> riscos genéricos de nuvem — são os que existem mesmo sem Azure/remoto.

## R1 — Escopo amplo do `filesystem` expõe segredos e arquivos sensíveis  🔴 Alto

**Descrição.** O reference `filesystem` server dá acesso a **tudo** dentro de cada raiz
concedida. Se alguém configurar a raiz como `.` (o repositório inteiro) — atalho tentador —, o
agente passa a poder **ler** `.env`, `.git/config`, credenciais em `infra/parameters/*.bicepparam`
e qualquer segredo, e **escrever/sobrescrever** qualquer arquivo. Um prompt malicioso (ou um
chunk envenenado) poderia induzir o agente a exfiltrar ou apagar conteúdo.

**Evidência de que a mitigação está aplicada.** O `list_allowed_directories` real (ver
`mcp-evidence.md`) mostra que o server enxerga **apenas** `docs data specs src skills prompts` —
`.env`, `.git/` e `infra/` ficam **fora do alcance**.

**Mitigações acionáveis.**
1. **Least privilege de raízes** (feito): conceder só as 6 pastas de trabalho, nunca `.`.
2. **`.gitignore` + sem segredos no escopo**: manter `.env` e parâmetros fora das pastas
   concedidas; segredos via variáveis de ambiente do processo, não em arquivo lido pelo agente.
3. **Auditoria**: `list_allowed_directories` deve ser checado no health check (Tech Lead 2.2).

## R2 — Fontes de verdade graváveis: o reference server não tem read-only nativo  🟠 Médio

**Descrição.** `docs/novatech/` e `data/retrieval-corpus/` são **fontes de verdade** que o
agente só deveria **ler**. Mas o `filesystem` server expõe `write_file`/`edit_file`/`move_file`
para **todas** as raízes concedidas — não há flag "esta raiz é read-only". Um agente poderia
alterar um documento normativo ou um chunk, corrompendo silenciosamente a base de RAG (e, com
isso, as respostas ao cliente).

**Mitigações acionáveis.**
1. **Política explícita** no AGENTS.md: "agentes NÃO escrevem em `docs/novatech/` nem
   `data/retrieval-corpus/`".
2. **Auditoria via `git` MCP**: qualquer escrita aparece em `git status`/`git diff` e é
   **barrada no validation gate de code review** (Gate 3 — Code → Merge).
3. **Reforço técnico**: rodar uma 2ª instância do `filesystem` **só com `./docs ./data`** num
   perfil de agente "leitor" (sem usar as tools de escrita), ou aplicar ACL read-only do SO.

## R3 — Execução de código de terceiros em runtime (`npx -y` / `uvx`)  🟠 Médio

**Descrição.** `npx -y @modelcontextprotocol/server-...` e `uvx mcp-server-git` **baixam e
executam** pacotes a cada invocação. Sem pin de versão, uma versão comprometida do pacote
(supply-chain) roda com as permissões do dev e o acesso ao repositório.

**Mitigações acionáveis.**
1. **Pin de versão** no `.mcp/mcp.json` (ex.: `@modelcontextprotocol/server-filesystem@2025.x`)
   em vez de "última".
2. **Lockfile / cache offline**: instalar os servers como devDependencies e invocar do cache,
   evitando download dinâmico.
3. **Revisão de adição de server** (política do Tech Lead 2.2): nenhum server novo entra no
   `.mcp/mcp.json` sem revisão de escopo e origem do pacote.

## R4 — Memória persistente pode reter contexto sensível entre sessões  🟡 Baixo

**Descrição.** O `memory` server grava um grafo **persistente** em disco. Glossário e decisões
são desejáveis, mas o agente pode acabar gravando trechos sensíveis (dados de cliente, valores
contratuais) que ficam disponíveis em sessões/contextos futuros sem controle de acesso.

**Mitigações acionáveis.**
1. **Política de conteúdo**: gravar no `memory` apenas linguagem ubíqua e decisões de
   arquitetura — nunca dados de cliente ou segredos.
2. **Arquivo de grafo no `.gitignore`** e fora do escopo do `filesystem` server.
3. **Revisão periódica** do grafo (`read_graph`) no health check.

---

## Resumo

| Risco | Severidade | Mitigação principal | Estado |
|-------|-----------|---------------------|--------|
| R1 — escopo amplo expõe segredos | 🔴 Alto | least privilege de raízes (não usar `.`) | ✅ aplicado (evidência: `list_allowed_directories`) |
| R2 — fontes de verdade graváveis | 🟠 Médio | política + auditoria git + 2ª instância read-only | ✅ política/auditoria; reforço opcional |
| R3 — código de terceiros em runtime | 🟠 Médio | pin de versão + revisão de adição de server | 📋 recomendado |
| R4 — memória persistente sensível | 🟡 Baixo | política de conteúdo + gitignore | 📋 recomendado |
