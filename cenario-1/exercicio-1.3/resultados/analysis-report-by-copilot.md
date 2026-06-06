## Relatório de Avaliação do Retrieval — NovaTech RAG PoC

---

### Pergunta 1

**"Qual o prazo de devolução para carga padrão?"**

### Resultados Recuperados

| Ranking | Chunk                             | Fonte                      | Score  |
| ------- | --------------------------------- | -------------------------- | ------ |
| 1       | Seção 3.5 — Custos de devolução   | POL-001 (formal)           | 0.836  |
| 2       | Item 22 — Seguro de carga         | FAQ-atendimento (informal) | 0.8114 |
| 3       | Item 38 — Carga danificada        | FAQ-atendimento (informal) | 0.7935 |
| 4       | Item 3 — Devolução carga perigosa | FAQ-atendimento (informal) | 0.7829 |

### Comparação com o Gabarito

- Chunk esperado (primário): **POL-001-A** (Seção 3.1: Prazo geral — 7 dias úteis) e **POL-001-B** (Seção 3.2: Exceções)
- Chunk recuperado: **POL-001-D** (Seção 3.5: Custos) + 3 chunks informais do FAQ
- Corresponde ao esperado? **Não** — recuperou a seção de custos em vez da seção de prazo

### Análise

- **O retrieval foi adequado?** Parcialmente. O documento correto (POL-001) foi identificado, mas a seção errada ficou no topo.
- **Houve documentos irrelevantes?** Sim — FAQ sobre seguro de carga (Item 22) é irrelevante para a pergunta sobre prazo de devolução.
- **Indícios de problemas de chunking?** Sim — a seção 3.1 (prazo geral) provavelmente não contém o termo "carga padrão" explicitamente, enquanto a seção 3.5 menciona "devolução" múltiplas vezes com mais contexto semântico.
- **Indícios de problemas de relevância?** Sim — o embedding de "prazo de devolução para carga padrão" se aproximou mais de "custos de devolução" do que de "prazo geral de 7 dias úteis". O modelo MiniLM não distinguiu bem a intenção temporal.

---

### Pergunta 2

**"Qual o multiplicador de frete para região Norte?"**

### Resultados Recuperados

| Ranking | Chunk                                              | Fonte                      | Score  |
| ------- | -------------------------------------------------- | -------------------------- | ------ |
| 1       | Seção 2.1 — Multiplicadores regionais              | PROC-042-v1 (formal)       | 0.8212 |
| 2       | Seção 2.1 — Multiplicadores atualizados (nov/2023) | PROC-042-v2 (formal)       | 0.8025 |
| 3       | Item 8 — Frete especial                            | FAQ-atendimento (informal) | 0.7406 |
| 4       | Item 15 — Tier Platinum                            | FAQ-atendimento (informal) | 0.7244 |

### Comparação com o Gabarito

- Chunk esperado (primário): **PROC-042v2-B** (multiplicadores atualizados, Norte = 1.8)
- Chunks que podem aparecer: **PROC-042-B** (versão antiga, Norte = 1.6)
- Chunk recuperado: Ambas as versões foram recuperadas (v1 em 1º, v2 em 2º)
- Corresponde ao esperado? **Parcialmente** — os dois chunks corretos estão presentes, mas a **versão obsoleta (v1) ficou acima da versão vigente (v2)**

### Análise

- **O retrieval foi adequado?** Sim para recall (ambas as versões foram recuperadas), mas a **ordenação é problemática** — a v1 obsoleta está em 1º lugar.
- **Houve documentos irrelevantes?** FAQ-15 (tier Platinum) é irrelevante.
- **Indícios de problemas de chunking?** Não — os chunks de tabela foram preservados corretamente como unidades inteiras.
- **Indícios de problemas de relevância?** Sim — **risco de conflito de versão** confirmado. Sem o filtro de penalização de versão (previsto na arquitetura mas não implementado na PoC), a v1 pode ser usada pelo LLM como resposta primária (Norte = 1.6 em vez de 1.8).

---

### Pergunta 3

**"Qual o SLA de atendimento para cliente Gold?"**

### Resultados Recuperados

| Ranking | Chunk                               | Fonte                      | Score  |
| ------- | ----------------------------------- | -------------------------- | ------ |
| 1       | Seção 5 — Medição e reportes        | SLA-2024 (formal)          | 0.8329 |
| 2       | Item 15 — Tier Platinum             | FAQ-atendimento (informal) | 0.8211 |
| 3       | Seção 1 — Classificação de clientes | SLA-2024 (formal)          | 0.8049 |
| 4       | Seção 4 — Penalidades               | SLA-2024 (formal)          | 0.8032 |

### Comparação com o Gabarito

- Chunk esperado (primário): **SLA-2024-B** (Tabela de SLAs — Gold: resposta 2h, resolução 24h)
- Chunks secundários: **SLA-2024-A** (Classificação), **SLA-2024-C** (Incidentes críticos)
- Chunk recuperado: Seções 5, 1 e 4 do SLA — **mas a seção 2 (tabela de SLAs) não apareceu**
- Corresponde ao esperado? **Não** — o chunk mais importante (tabela com os tempos) não foi recuperado

### Análise

- **O retrieval foi adequado?** Não. O documento correto foi identificado (SLA-2024 aparece 3 vezes), mas a seção crucial com os tempos de SLA (2h/24h) está ausente.
- **Houve documentos irrelevantes?** Sim — FAQ-15 (tier Platinum) em 2º lugar é irrelevante; provavelmente recuperado por menção a "Gold, Silver e Standard".
- **Indícios de problemas de chunking?** Provável — a tabela de SLA com os tempos pode ter sido dividida ou o embedding da tabela Markdown não captura bem a relação "Gold → 2h resposta".
- **Indícios de problemas de relevância?** Sim — a seção de medição (como o SLA é calculado) ficou acima da tabela de valores (o que é o SLA de fato). O modelo confundiu "informação sobre SLA" com "valores do SLA".

---

### Pergunta 4

**"Como funciona o frete para cargas acima de 500kg?"**

### Resultados Recuperados

| Ranking | Chunk                         | Fonte                      | Score  |
| ------- | ----------------------------- | -------------------------- | ------ |
| 1       | Seção 1 — Objetivo            | PROC-042-v1 (formal)       | 0.8294 |
| 2       | Seção 1 — Objetivo            | PROC-042-v2 (formal)       | 0.8177 |
| 3       | Item 22 — Seguro de carga     | FAQ-atendimento (informal) | 0.8157 |
| 4       | Seção 4 — Condições especiais | PROC-042-v1 (formal)       | 0.8101 |

### Comparação com o Gabarito

- Chunk esperado (primário): **PROC-042v2-B** (multiplicadores), **PROC-042v2-A** (fórmula com fatores de peso)
- Chunks que podem aparecer: **PROC-042-B** (versão antiga)
- Chunk recuperado: Seções de "Objetivo" (introdução) + Condições especiais
- Corresponde ao esperado? **Parcialmente** — os documentos corretos foram identificados, mas as seções recuperadas são introdutórias/complementares, não as que contêm a fórmula e os multiplicadores

### Análise

- **O retrieval foi adequado?** Parcialmente. Os documentos fonte são corretos (PROC-042 v1 e v2), mas as seções de "Objetivo" são descritivas e não contêm a fórmula operacional.
- **Houve documentos irrelevantes?** Sim — FAQ-22 (seguro de carga) em 3º lugar é completamente irrelevante.
- **Indícios de problemas de chunking?** Sim — a seção "Objetivo" é um chunk curto que menciona "500kg" diretamente, o que a torna semanticamente próxima da pergunta apesar de ter pouco conteúdo útil. A fórmula e tabela (chunks mais úteis) provavelmente contêm termos mais técnicos e menos similares à pergunta em linguagem natural.
- **Indícios de problemas de relevância?** Sim — menção explícita de "500kg" na seção de objetivo dá vantagem de similaridade lexical sobre a seção com a fórmula real.

---

### Pergunta 5

**"Posso devolver carga perigosa?"**

### Resultados Recuperados

| Ranking | Chunk                               | Fonte                      | Score  |
| ------- | ----------------------------------- | -------------------------- | ------ |
| 1       | Item 22 — Seguro de carga           | FAQ-atendimento (informal) | 0.7901 |
| 2       | Item 3 — Devolução carga perigosa   | FAQ-atendimento (informal) | 0.7798 |
| 3       | Item 38 — Carga danificada          | FAQ-atendimento (informal) | 0.7718 |
| 4       | Seção 3.2 — Exceções ao prazo geral | POL-001 (formal)           | 0.7471 |

### Comparação com o Gabarito

- Chunk esperado (primário): **POL-001-B** (Seção 3.2 — "cargas perigosas NÃO são elegíveis")
- Chunks secundários: **FAQ-03**, **POL-001-A**
- Chunk recuperado: POL-001-B aparece em 4º lugar; FAQ-03 em 2º; 1º e 3º são irrelevantes
- Corresponde ao esperado? **Parcialmente** — os chunks esperados foram recuperados, mas o **chunk formal autoritativo (POL-001-B) ficou em último lugar**, abaixo de 3 chunks informais

### Análise

- **O retrieval foi adequado?** Problemático. O chunk que contém a resposta correta e autoritativa (POL-001-B: cargas perigosas NÃO podem ser devolvidas) ficou em 4º lugar com score 0.7471, enquanto fontes informais dominaram o topo.
- **Houve documentos irrelevantes?** Sim — FAQ-22 (seguro de carga) em 1º lugar é irrelevante. Provavelmente recuperado por mencionar "cargas perigosas" no contexto de seguro.
- **Indícios de problemas de chunking?** Sim — o FAQ tem chunks mais curtos e coloquiais que se aproximam semanticamente de perguntas em linguagem natural ("pode devolver carga perigosa?" ≈ "Cliente perguntou se pode devolver carga perigosa").
- **Indícios de problemas de relevância?** Sim — **risco crítico de inversão de fonte**: o FAQ informal ficou acima do documento normativo POL-001. Se o LLM construir a resposta a partir dos primeiros chunks, pode usar informação não validada.

---

## Resumo Consolidado

### Taxa de Acerto do Retrieval

| Pergunta                | Chunk primário esperado no top-4? | Posição                     | Veredicto                        |
| ----------------------- | --------------------------------- | --------------------------- | -------------------------------- |
| 1 — Prazo devolução     | POL-001-A (prazo)                 | **Ausente**                 | ❌ Falha                         |
| 2 — Multiplicador Norte | PROC-042v2-B                      | 2º lugar                    | ⚠️ Parcial (v1 acima)            |
| 3 — SLA Gold            | SLA-2024-B (tabela)               | **Ausente**                 | ❌ Falha                         |
| 4 — Frete >500kg        | PROC-042v2-A/B (fórmula)          | **Ausente** (só "Objetivo") | ⚠️ Parcial                       |
| 5 — Carga perigosa      | POL-001-B (exceções)              | 4º lugar                    | ⚠️ Parcial (abaixo de informais) |

**Taxa de acerto total: 0/5 acertos plenos, 3/5 parciais, 2/5 falhas**

---

### Principais Problemas Encontrados

1. **Dominância do FAQ informal** — Em 4 das 5 perguntas, chunks do FAQ aparecem no top-3, frequentemente acima dos documentos formais. O FAQ usa linguagem coloquial que se aproxima mais de perguntas em linguagem natural.

2. **Seções introdutórias vencendo seções operacionais** — Chunks de "Objetivo" e "Custos" (que mencionam termos-chave) ficam acima dos chunks que contêm as regras efetivas (fórmulas, tabelas, prazos).

3. **Ausência do filtro de versão** — PROC-042 v1 (obsoleta) aparece consistentemente acima da v2 (vigente), provavelmente por ter texto mais curto e denso.

4. **Tabelas Markdown com baixa recuperabilidade** — As tabelas de SLA e multiplicadores (chunks mais valiosos) parecem gerar embeddings menos eficazes que texto corrido.

---

### Possíveis Melhorias

| Melhoria                                                                   | Impacto esperado                                                                |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Implementar separação formal/informal** (duas coleções)                  | Garante que fontes formais sejam priorizadas — conforme previsto na arquitetura |
| **Filtro de penalização de versão** (v1 × 0.7)                             | Resolve o problema PROC-042 v1 vs v2                                            |
| **Adicionar query expansion** — reformular a pergunta para termos técnicos | "Prazo de devolução" → buscar também "7 dias úteis", "prazo geral"              |
| **Aumentar top_k para 6-8** e aplicar reranking                            | Com mais candidatos, o chunk correto entra no pool e pode ser repriorizado      |
| **Prefixar tabelas com descrição textual** antes de gerar embedding        | "Tabela de SLA: Gold resposta 2h resolução 24h..." melhora o embedding          |
| **Usar modelo de embedding maior** (all-mpnet-base-v2, 768d)               | Melhor compreensão semântica, especialmente para tabelas                        |
