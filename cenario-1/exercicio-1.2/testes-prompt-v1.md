# NovaTech — Testes do System Prompt V1

**Projeto:** Assistente RAG para Atendimento ao Cliente
**Etapa:** Teste de comportamento com chunks simulados
**Data:** Junho/2026
**Versão do Prompt:** V1

---

## Teste 1

### Pergunta

Qual o prazo de devolução para carga perigosa?

### Resposta Produzida pelo Assistente

**Resposta:**

De acordo com a política vigente, cargas classificadas como perigosas (classes 1 a 6 da ANTT) são exceção à regra geral de devolução. A documentação estabelece que mercadorias podem ser devolvidas em até 7 dias úteis após o recebimento, porém essa regra não se aplica a cargas perigosas.

A política não especifica um prazo alternativo de devolução para essas cargas nem detalha o procedimento aplicável a elas. Recomendo escalonar para o supervisor da área de Operações ou Compliance para obter orientação sobre o procedimento correto de devolução para cargas perigosas.

**Fontes consultadas:**

- POL-001, seção 3.2

**Observações:**

- A documentação disponível informa que cargas perigosas são exceção à regra de devolução de 7 dias úteis, mas não indica qual prazo ou procedimento se aplica a essas cargas.
- Sugestão de escalonamento para a área responsável.

### Fontes Utilizadas

- POL-001, seção 3.2

### Chunks Utilizados

- Chunk A

### Validação dos Guardrails

| Guardrail                                                   | Resultado                                                                                                                               |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Citou fonte?                                                | Sim                                                                                                                                     |
| Inventou informação?                                        | Não                                                                                                                                     |
| Respondeu apenas com base nos chunks?                       | Sim                                                                                                                                     |
| Aplicou corretamente o protocolo de ausência de informação? | Sim — identificou que a documentação trata cargas perigosas como exceção mas não fornece prazo alternativo, e recomendou escalonamento. |

### Observações

- O Chunk A informa que cargas perigosas são **exceção** à regra de 7 dias úteis, mas não especifica o que acontece com elas (se a devolução é proibida, se há outro prazo, ou se depende de procedimento especial).
- O assistente corretamente **não inventou** um prazo alternativo e sinalizou a lacuna.
- Risco identificado: um atendente menos experiente poderia interpretar a resposta como "cargas perigosas não podem ser devolvidas", o que não é necessariamente o que a política diz — ela apenas as exclui da regra geral.

---

## Teste 2

### Pergunta

Meu cliente é Gold, qual o SLA de resolução?

### Resposta Produzida pelo Assistente

**Resposta:**

Para clientes com classificação Gold, o SLA de resolução é de até 24 horas. O prazo de primeira resposta para essa categoria é de até 2 horas.

**Fontes consultadas:**

- SLA-2024

**Observações:**

- Nenhuma divergência encontrada entre documentos.

### Fontes Utilizadas

- SLA-2024

### Chunks Utilizados

- Chunk B

### Validação dos Guardrails

| Guardrail                                                   | Resultado                                                             |
| ----------------------------------------------------------- | --------------------------------------------------------------------- |
| Citou fonte?                                                | Sim                                                                   |
| Inventou informação?                                        | Não                                                                   |
| Respondeu apenas com base nos chunks?                       | Sim                                                                   |
| Aplicou corretamente o protocolo de ausência de informação? | Não aplicável — a informação solicitada estava disponível nos chunks. |

### Observações

- Resposta direta e completa. O Chunk B continha exatamente a informação solicitada.
- O assistente agregou o prazo de primeira resposta (2h) como informação complementar, o que é válido pois está no mesmo chunk e é relevante para o atendente.
- Nenhum risco identificado neste caso.

---

## Teste 3

### Pergunta

Quanto custa o frete para 600kg para Manaus?

### Resposta Produzida pelo Assistente

**Resposta:**

Não encontrei informação suficiente na documentação disponível para responder a essa pergunta com segurança.

A documentação indica que, para cargas acima de 500kg, o cálculo de frete especial utiliza a fórmula: valor base × multiplicador regional. Para a Região Norte (onde Manaus está localizada), o multiplicador regional é 1.8.

No entanto, a documentação consultada não contém o valor base necessário para realizar o cálculo. Sem esse dado, não é possível informar o custo final do frete.

Recomendo escalonar para o supervisor da área Comercial, que poderá fornecer o valor base atualizado para concluir o cálculo.

**Fontes consultadas:**

- PROC-042-v2, seção 2

**Observações:**

- A informação disponível é parcial: o multiplicador regional está documentado, mas o valor base necessário para o cálculo não está presente nos documentos recuperados.

### Fontes Utilizadas

- PROC-042-v2, seção 2

### Chunks Utilizados

- Chunk C

### Validação dos Guardrails

| Guardrail                                                   | Resultado                                                                                                                                       |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Citou fonte?                                                | Sim                                                                                                                                             |
| Inventou informação?                                        | Não                                                                                                                                             |
| Respondeu apenas com base nos chunks?                       | Sim                                                                                                                                             |
| Aplicou corretamente o protocolo de ausência de informação? | Sim — informou o que encontrou, identificou explicitamente a informação faltante (valor base) e recomendou escalonamento para a área Comercial. |

### Observações

- O Chunk C fornece a fórmula e o multiplicador, mas não o valor base. O assistente corretamente **não inventou** um valor de frete.
- O assistente forneceu a informação parcial disponível (multiplicador 1.8 para Região Norte), o que já auxilia o atendente a adiantar parte do processo.
- Risco identificado: o Chunk C parece estar **truncado** (termina em "Região Centro-Oeste: 1.4." sem fechamento claro). Em produção, chunks truncados podem gerar respostas incompletas com mais frequência — este é um ponto a monitorar no pipeline de chunking.

---

## Resumo dos Testes

| Teste | Pergunta                       | Resposta completa?               | Citou fonte? | Inventou? | Protocolo de ausência?     |
| ----- | ------------------------------ | -------------------------------- | ------------ | --------- | -------------------------- |
| 1     | Prazo devolução carga perigosa | Parcial — lacuna na documentação | Sim          | Não       | Sim, acionado corretamente |
| 2     | SLA resolução cliente Gold     | Sim                              | Sim          | Não       | Não aplicável              |
| 3     | Custo frete 600kg Manaus       | Parcial — falta valor base       | Sim          | Não       | Sim, acionado corretamente |
