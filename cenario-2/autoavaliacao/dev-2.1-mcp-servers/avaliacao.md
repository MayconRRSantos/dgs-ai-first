# Avaliação do Exercício 2.1 — Desenvolvedor (MCP servers)

> Autoavaliação seguindo `avaliacao-foundation.md` + `avaliacao-desenvolvedor.md` + `prompt-avaliacao.md`.

### Resumo

Entregável completo e tecnicamente sólido: os 4 servers locais foram mapeados e **executados de
verdade** (transcrição real de JSON-RPC, não screenshot), com least privilege comprovado via
`list_allowed_directories` e recuperação do chunk `SLA-2024-B` batendo com o gabarito do Anexo B.
A análise de riscos é específica ao setup local e reconhece honestamente a limitação do reference
server (sem read-only nativo).

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | **3** | Mapeia cada necessidade a um reference server local; distingue tools/resources/prompts; least privilege concreto (filesystem com escopo mínimo, `docs/novatech` e `data/retrieval-corpus` read-only) — exatamente o exemplo score-3 da foundation. |
| D2 — Uso de Ferramentas | **3** | Evidência de execução **real**: cliente MCP stdio fez `initialize`→`tools/list`→`tools/call` contra `filesystem` (v0.2.0, 14 tools) e `git` (v1.28.0, 12 tools), com saída crua de leitura de doc, recuperação de chunk e `git_log`. Reproduzível (`mcp-evidence-client.mjs` versionado). Atende a regra de corte "Dev 2.1 sem evidência real → D2 ≤ 1" com folga. |
| D3 — Qualidade do Entregável | **3** | `.mcp/mcp.json` JSON válido (verificado) e coerente com o mapeamento; docs completas, machine-actionable, específicas ao NovaTech. Outro dev usaria sem pedir esclarecimento. |
| D4 — Pensamento Crítico | **3** | Honestidade técnica: não inventou flag read-only inexistente (transformou em risco R2); documentou o quirk do `search_files`; expôs e resolveu o gap de ambiente `uv/uvx`. 4 riscos com severidade e mitigação acionável. |
| D5 — Aplicabilidade ao Projeto | **3** | Respeita Anexo C; usa as fontes reais (Confluence→`docs/novatech`, Azure AI Search→`data/retrieval-corpus`, GitHub→`git`); recuperação coerente com o mapa de cobertura do Anexo B; planejamento referencia ADR-0001/0002/0003/0004. |

**Score do exercício: 3.0**

### Verificação de Artefatos Machine-Readable

- `.mcp/mcp.json`: prescritivo e parseável (JSON válido; um host MCP consome direto). ✅
- `mcp-mapping.md`: tabelas estruturadas necessidade→server→escopo, primitivas reais. ✅
- Nada narrativo-demais; cada afirmação técnica tem respaldo na execução real.

### Pontos Fortes

1. Evidência **verificável e reproduzível** (transcrição + script versionado) — mais forte que screenshot.
2. Least privilege não é declarado, é **comprovado** (`list_allowed_directories` mostra `.env`/`.git`/`infra` fora do alcance).
3. Honestidade sobre limitações (read-only não-nativo, `search_files`, `uv` ausente) → vira insumo da análise de riscos.

### Pontos de Melhoria

1. **Transparência de ferramenta:** o enunciado cita "Claude/Copilot com servers ativos"; usei um host MCP programático. É evidência equivalente/superior, mas convém anexar também um print do agente interativo consumindo os mesmos servers, se for exigida a ferramenta nominal.
2. **Hardening recomendado mas não aplicado:** pin de versão dos pacotes `npx -y`/`uvx` (R3) e 2ª instância read-only do filesystem (R2) ficaram como recomendação — poderiam ser demonstrados.

### Classificação

**Aprovado com distinção (3.0)**

### Tópicos da Trilha para Reforço

Nenhum (score ≥ 2.5).
