# NovaTech — Context Engineering: System Prompt V1 e Arquitetura de Contexto

**Projeto:** Assistente RAG para Atendimento ao Cliente
**Cliente:** NovaTech Logística
**Elaborado por:** DB1
**Data:** Junho/2026
**Versão:** 1.0 — Discovery

---

## 1. System Prompt V1 (Completo)

```xml
<identidade>
Você é o Assistente NovaTech, uma ferramenta interna de apoio à equipe de atendimento ao cliente
da NovaTech Logística. Seu papel é responder perguntas sobre procedimentos, políticas, prazos,
regras de frete, SLAs e normas da empresa, sempre com base exclusiva na documentação oficial
fornecida nos chunks de contexto abaixo.

Você NÃO é um chatbot público. Você atende apenas colaboradores internos (atendentes) que
precisam de informações rápidas e confiáveis para resolver chamados de clientes.
</identidade>

<regras>
1. Responda SOMENTE com base nas informações presentes nos chunks fornecidos nesta conversa.
2. NUNCA invente, extrapole ou suponha prazos, valores, políticas ou procedimentos que não
   estejam explicitamente nos chunks.
3. Cite SEMPRE a fonte documental (código do documento, seção e versão) ao final de cada
   informação relevante na resposta.
4. Se dois ou mais chunks apresentarem informações contraditórias sobre o mesmo assunto:
   a. Priorize o documento com data de vigência mais recente.
   b. Informe o atendente sobre a divergência encontrada.
   c. Recomende validação com o supervisor da área responsável.
5. Responda em português formal, mas acessível — evite jargão técnico desnecessário.
6. Não responda perguntas fora do escopo da documentação da NovaTech (ex: dúvidas pessoais,
   assuntos externos à empresa).
7. Não forneça opiniões, interpretações jurídicas ou recomendações que extrapolem o texto
   documental.
</regras>

<prioridade_entre_fontes>
Quando múltiplos documentos forem recuperados, aplique esta hierarquia de confiabilidade:

1. Políticas vigentes (prefixo POL-) — maior autoridade normativa.
2. Procedimentos operacionais (prefixo PROC-) — instruções de execução.
3. Tabelas de SLA (prefixo SLA-) — parâmetros contratuais.
4. Planilhas de referência (pasta de rede) — dados operacionais atualizados mensalmente.
5. Páginas da Wiki (Confluence) — conteúdo de apoio e orientações complementares.

Em caso de conflito entre fontes de mesma hierarquia, prevalece o documento com data de
atualização mais recente. Sempre indique a data de vigência quando disponível.
</prioridade_entre_fontes>

<uso_dos_chunks>
Os chunks a seguir foram recuperados automaticamente a partir da pergunta do atendente.
Cada chunk contém:
- O trecho relevante da documentação.
- A fonte (código, seção e versão do documento).
- O score de relevância (metadata interna — não exibir ao usuário).

Instruções para uso dos chunks:
- Leia TODOS os chunks antes de formular a resposta.
- Utilize apenas chunks cuja informação seja diretamente relevante à pergunta.
- Se um chunk for parcialmente relevante, extraia somente a parte aplicável.
- Se nenhum chunk for relevante, siga o protocolo de ausência de informação.
- Não mencione a mecânica de recuperação (RAG, chunks, embeddings) na resposta ao atendente.
</uso_dos_chunks>

<ausencia_de_informacao>
Se os chunks fornecidos NÃO contiverem informação suficiente para responder à pergunta:

1. Informe de forma clara:
   "Não encontrei informação suficiente na documentação disponível para responder a essa
   pergunta com segurança."
2. Sugira o próximo passo:
   "Recomendo escalonar para o supervisor da área [Operações/Compliance/Comercial] para
   validação."
3. Se possível, indique QUAL informação está faltando:
   "A documentação atual não cobre [aspecto específico]. Pode ser necessário consultar
   a área responsável."

NUNCA tente "completar" a resposta com suposições quando a informação for insuficiente.
</ausencia_de_informacao>

<formato_de_resposta>
Estruture toda resposta no seguinte formato:

**Resposta:**
[Resposta direta e objetiva à pergunta, em 1 a 3 parágrafos curtos.]

**Fontes consultadas:**
- [Código do documento, seção, versão — para cada fonte utilizada]

**Observações (quando aplicável):**
- [Divergências encontradas entre documentos]
- [Limitações da informação disponível]
- [Sugestão de escalonamento, se necessário]
</formato_de_resposta>
```

---

## 2. Mapeamento de Contexto Estático vs. Dinâmico

### 2.1 Contexto Estático

Componentes que são **fixos em toda requisição** — compõem o system prompt e não variam entre chamados.

| Componente                   | Tag XML                     | Muda quando?                              | Responsável pela atualização |
| ---------------------------- | --------------------------- | ----------------------------------------- | ---------------------------- |
| Identidade do assistente     | `<identidade>`              | Apenas se o escopo do projeto mudar       | DB1 (time de projeto)        |
| Regras e guardrails          | `<regras>`                  | Revisão trimestral ou por incidente       | DB1 + NovaTech (Compliance)  |
| Hierarquia de fontes         | `<prioridade_entre_fontes>` | Quando houver nova categoria de documento | DB1 + NovaTech (Operações)   |
| Instruções de uso dos chunks | `<uso_dos_chunks>`          | Apenas se a arquitetura RAG mudar         | DB1 (time técnico)           |
| Protocolo de ausência        | `<ausencia_de_informacao>`  | Revisão trimestral                        | DB1 + NovaTech (Atendimento) |
| Formato de resposta          | `<formato_de_resposta>`     | Quando o formato de saída for ajustado    | DB1 + NovaTech (Atendimento) |

### 2.2 Contexto Dinâmico

Componentes que são **injetados a cada requisição** — montados pelo pipeline de orquestração.

| Componente                      | Exemplo                                          | Origem                            | Injetado por               |
| ------------------------------- | ------------------------------------------------ | --------------------------------- | -------------------------- |
| Pergunta do atendente           | "Qual o prazo de devolução para carga perigosa?" | Input do usuário no Teams         | Gateway de integração      |
| Chunks recuperados              | Chunk A (POL-001), Chunk C (PROC-042-v2)         | Azure AI Search (índice vetorial) | Pipeline RAG               |
| Dados do cliente em atendimento | "Cliente: Transportes Iguaçu — Tier: Gold"       | CRM / sistema de chamados         | API de integração          |
| Histórico da conversa           | Últimas 3 interações do mesmo chamado            | Memória de sessão                 | Orquestrador de conversa   |
| Metadados de recuperação        | Score de similaridade, data do documento, versão | Azure AI Search                   | Pipeline RAG (uso interno) |

### 2.3 Template de Montagem da Requisição

```
┌─────────────────────────────────────────────┐
│  SYSTEM MESSAGE                             │
│  ┌────────────────────────────────────────┐ │
│  │ Contexto Estático (fixo)               │ │
│  │  ├─ <identidade>                       │ │
│  │  ├─ <regras>                           │ │
│  │  ├─ <prioridade_entre_fontes>          │ │
│  │  ├─ <uso_dos_chunks>                   │ │
│  │  ├─ <ausencia_de_informacao>           │ │
│  │  └─ <formato_de_resposta>              │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ Contexto Dinâmico (por requisição)     │ │
│  │  ├─ <dados_do_cliente>                 │ │
│  │  └─ <chunks_recuperados>               │ │
│  └────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  USER MESSAGES                              │
│  ├─ Histórico da conversa (até 3 turnos)  │
│  └─ Pergunta atual do atendente           │
├─────────────────────────────────────────────┤
│  ASSISTANT MESSAGE                          │
│  └─ Resposta gerada pelo modelo           │
└─────────────────────────────────────────────┘
```

---

## 3. Estimativa de Tokens por Componente

As estimativas abaixo consideram tokenização típica para português em modelos da família Claude (aproximadamente 1 token a cada 3–4 caracteres em português).

| Componente                            | Tipo     | Estimativa (tokens) | % do contexto típico |
| ------------------------------------- | -------- | ------------------- | -------------------- |
| `<identidade>`                        | Estático | ~120                | 3%                   |
| `<regras>`                            | Estático | ~250                | 7%                   |
| `<prioridade_entre_fontes>`           | Estático | ~180                | 5%                   |
| `<uso_dos_chunks>`                    | Estático | ~170                | 5%                   |
| `<ausencia_de_informacao>`            | Estático | ~150                | 4%                   |
| `<formato_de_resposta>`               | Estático | ~130                | 4%                   |
| **Subtotal Estático**                 | —        | **~1.000**          | **~28%**             |
| `<dados_do_cliente>`                  | Dinâmico | ~50–80              | 2%                   |
| `<chunks_recuperados>` (3–5 chunks)   | Dinâmico | ~800–1.500          | 35%                  |
| Histórico de conversa (até 3 turnos)  | Dinâmico | ~400–800            | 20%                  |
| Pergunta atual                        | Dinâmico | ~30–80              | 2%                   |
| **Subtotal Dinâmico**                 | —        | **~1.300–2.500**    | **~62%**             |
| **Overhead de formatação (XML tags)** | —        | **~100**            | **~3%**              |
| **TOTAL ESTIMADO**                    | —        | **~2.400–3.600**    | **100%**             |

**Observações sobre a estimativa:**

- O orçamento total por requisição fica confortavelmente abaixo de 5.000 tokens de entrada, deixando ampla margem para a resposta do modelo (tipicamente 200–500 tokens).
- O componente mais variável é `<chunks_recuperados>`: a recomendação é limitar cada chunk a ~300 tokens e recuperar no máximo 5 chunks por consulta, totalizando o teto de ~1.500 tokens.
- Se o histórico de conversa crescer além de 3 turnos, aplicar sumarização dos turnos anteriores para manter o orçamento.

---

## 4. Justificativa da Ordem dos Componentes

A ordem dos blocos no system prompt não é arbitrária. Ela segue três princípios de design cognitivo para LLMs:

### 4.1 Princípio da Primazia — O que vem primeiro define o papel

O bloco `<identidade>` abre o prompt porque estabelece **quem** o modelo é antes de dizer **o que** ele deve fazer. Modelos de linguagem calibram o estilo, o tom e o escopo de suas respostas a partir da identidade definida nas primeiras linhas. Colocar regras ou chunks antes da identidade aumenta o risco de respostas genéricas.

### 4.2 Princípio do Funil — Do geral para o específico

A sequência segue um afunilamento progressivo:

1. **Identidade** → Quem sou eu?
2. **Regras** → O que eu posso e não posso fazer?
3. **Prioridade entre fontes** → Como eu hierarquizo informações?
4. **Uso dos chunks** → Como eu processo o material recebido?
5. **Ausência de informação** → O que eu faço quando não sei?
6. **Formato de resposta** → Como eu entrego a resposta?

Cada bloco pressupõe o anterior. As regras fazem mais sentido depois que a identidade está definida; a prioridade entre fontes só é aplicável quando as regras já foram internalizadas.

### 4.3 Princípio da Recência — O que vem por último tem peso na geração

O bloco `<formato_de_resposta>` encerra o contexto estático intencionalmente. Como é o último bloco estático antes dos dados dinâmicos, ele atua como "última instrução" antes do modelo ver os chunks e a pergunta. Isso aumenta a aderência ao formato especificado — o modelo tende a seguir com mais fidelidade as instruções mais próximas do ponto de geração.

A sequência completa de proximidade ao ponto de geração fica:

```
[mais distante da geração]  Identidade → Regras → Hierarquia → Chunks → Formato
                                                                          ↓
                                         Dados do cliente → Histórico → Pergunta
                                                                          ↓
                                                                [ponto de geração]
```

---

## 5. Mitigação do Efeito "Lost in the Middle"

O problema de _Lost in the Middle_ refere-se à tendência documentada de LLMs darem menos atenção a informações posicionadas no meio do contexto, privilegiando o que está no início (primazia) e no final (recência).

### 5.1 Estratégias aplicadas neste prompt

**Estratégia 1 — Estrutura em XML com tags semânticas**

Cada bloco é delimitado por tags XML nomeadas (`<regras>`, `<chunks_recuperados>`, etc.). Isso funciona como "âncoras de atenção" — o modelo não precisa inferir onde um bloco começa e termina, porque a estrutura é explícita. Evidências empíricas mostram que delimitadores claros reduzem significativamente a perda de atenção em trechos intermediários.

**Estratégia 2 — Informações críticas nas bordas**

As duas informações mais importantes para a qualidade da resposta foram posicionadas nos extremos:

- **Início do prompt:** Identidade e regras (guardrails de segurança) — garantem que o modelo nunca "esqueça" que não pode inventar informações.
- **Final do contexto estático:** Formato de resposta — garante aderência estrutural.
- **Imediatamente antes da pergunta:** Chunks recuperados — ficam próximos do ponto de geração, maximizando a chance de serem utilizados.

**Estratégia 3 — Chunks ordenados por relevância decrescente**

No pipeline RAG, os chunks devem ser injetados em ordem de score de similaridade decrescente (o mais relevante primeiro). Assim, mesmo que o modelo perca atenção no meio da lista de chunks, os mais importantes já foram processados. Se houver 5 chunks e o modelo "perder" o 3º e o 4º, o impacto é minimizado porque os chunks 1, 2 e 5 (bordas) tendem a ser retidos.

**Estratégia 4 — Limitação da quantidade de chunks**

Mais chunks = maior zona intermediária = maior risco de perda. A recomendação é recuperar no máximo 5 chunks por consulta, com um tamanho máximo de ~300 tokens cada. Se o pipeline retornar mais candidatos, aplicar um corte por score mínimo de similaridade antes de injetar no contexto.

**Estratégia 5 — Redundância seletiva de guardrails**

A regra "NUNCA invente" aparece duas vezes no prompt: uma vez em `<regras>` (início) e uma variação reforçada em `<ausencia_de_informacao>` (meio-fim). Essa repetição intencional garante que o guardrail mais crítico do sistema não dependa de uma única posição no contexto.

### 5.2 Diagrama de risco por posição

```
Posição no contexto:    INÍCIO ████████░░░░░░░░████████ FINAL
Atenção do modelo:       ALTA   ████████░░░░░░░░████████  ALTA
                                         ↑
                                   ZONA DE RISCO
                                   (meio do contexto)

O que colocamos aqui:   Identidade │ Hierarquia │ Formato
                        Regras     │ Uso chunks │ Chunks
                                   │ Ausência   │ Pergunta
                        ──────────────────────────────────
                        GUARDRAILS   PROCESSUAL   OPERACIONAL
                        (não pode    (como fazer)  (fazer agora)
                         esquecer)
```

A zona de risco contém blocos processuais (hierarquia de fontes, instruções de uso de chunks) — informações importantes, mas que geram menor impacto se parcialmente ignoradas em uma resposta individual, pois os guardrails nas bordas continuam operando como rede de segurança.

---

## 6. Próximas Etapas (Fora do Escopo Desta Entrega)

Para referência do time, as etapas seguintes incluirão:

- **Teste com chunks simulados** — validar aderência ao formato e aos guardrails usando os Chunks A, B e C fornecidos.
- **Teste de contradição** — injetar chunks conflitantes para verificar se o protocolo de divergência é acionado.
- **Teste de ausência** — enviar perguntas sem chunks relevantes para validar o protocolo de escalonamento.
- **Refinamento iterativo** — ajustar pesos de instruções com base nos resultados dos testes.
- **Benchmark de latência** — medir tempo de resposta end-to-end para validar a meta de < 2 minutos.
