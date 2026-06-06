# NovaTech — Testes do System Prompt V2

**Projeto:** Assistente RAG para Atendimento ao Cliente
**Etapa:** Reteste com System Prompt V2
**Data:** Junho/2026
**Versão do Prompt:** V2

**Chunks disponíveis:** A (POL-001, seção 3.2), B (SLA-2024), C (PROC-042-v2, seção 2)
**Dados do cliente no contexto:** Nenhum (bloco `<dados_do_cliente>` ausente nesta simulação)

---

## Teste 1

### Pergunta

Qual o prazo de devolução para carga perigosa?

### Resposta Produzida pelo Assistente

**Resposta:**

A política de devoluções da NovaTech estabelece que mercadorias podem ser devolvidas em até 7 dias úteis após o recebimento. Contudo, o documento explicita que cargas classificadas como perigosas (classes 1 a 6 da ANTT) são exceção a essa regra.

A documentação recuperada não define qual prazo, procedimento ou restrição se aplica especificamente às cargas perigosas. Não é possível afirmar, com base neste documento, se a devolução é proibida, se há um prazo diferente, ou se há regulamentação externa aplicável — o texto apenas exclui essas cargas da regra geral de 7 dias úteis.

Para o procedimento geral de devolução (cargas não perigosas), o cliente deve abrir chamado no portal e anexar fotos da mercadoria. Não há confirmação na documentação de que esse mesmo procedimento se aplique às cargas perigosas.

Sugiro escalonar para o supervisor da área de Compliance ou Operações para obter o procedimento aplicável a cargas perigosas.

**Fontes consultadas:**

- POL-001, seção 3.2

**Observações:**

- A documentação contém uma exceção sem definição do procedimento alternativo. O termo "exceto" exclui cargas perigosas da regra geral, mas não estabelece a regra aplicável a elas.
- Escalonamento recomendado.

### Fontes Utilizadas

- POL-001, seção 3.2

### Chunks Utilizados

- Chunk A

### Guardrails Aplicados

| Guardrail                             | Aplicado?              | Detalhe                                                                                                                             |
| ------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Citou fonte                           | Sim                    | POL-001, seção 3.2                                                                                                                  |
| Não inventou informação               | Sim                    | Não atribuiu prazo alternativo nem interpretou a exceção                                                                            |
| Base exclusiva nos chunks             | Sim                    | Toda informação veio do Chunk A                                                                                                     |
| Protocolo de ausência                 | Sim — ausência parcial | Informou o que a documentação diz, identificou o que falta, recomendou escalonamento                                                |
| Tratamento de exceção (regra 9)       | Sim                    | Apresentou as três possibilidades sem escolher nenhuma                                                                              |
| Info complementar governada (regra 8) | Sim                    | Incluiu procedimento geral (abrir chamado, fotos) por ser do mesmo chunk e relevante, mas sinalizou que pode não se aplicar ao caso |
| Observações condicionais              | Sim                    | Seção incluída por haver exceção sem procedimento e escalonamento                                                                   |

---

## Teste 2

### Pergunta

Meu cliente é Gold, qual o SLA de resolução?

### Resposta Produzida pelo Assistente

**Resposta:**

Para clientes com classificação Gold, o SLA de resolução é de até 24 horas. O prazo de primeira resposta para essa categoria é de até 2 horas.

Observação: não há dados do cliente carregados no sistema para esta consulta. A classificação Gold foi considerada conforme informado por você. Caso deseje confirmar a classificação vigente do cliente, recomendo verificar no CRM.

**Fontes consultadas:**

- SLA-2024

### Fontes Utilizadas

- SLA-2024

### Chunks Utilizados

- Chunk B

### Guardrails Aplicados

| Guardrail                                             | Aplicado?         | Detalhe                                                                                                                                                                  |
| ----------------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Citou fonte                                           | Sim               | SLA-2024                                                                                                                                                                 |
| Não inventou informação                               | Sim               | Dados extraídos diretamente do Chunk B                                                                                                                                   |
| Base exclusiva nos chunks                             | Sim               | Toda informação veio do Chunk B                                                                                                                                          |
| Protocolo de ausência                                 | Não aplicável     | Informação completa disponível                                                                                                                                           |
| Uso de dados do cliente (bloco `<uso_dados_cliente>`) | Sim — instrução 3 | Bloco `<dados_do_cliente>` ausente; respondeu com base no que o atendente informou e sinalizou que não há dados do sistema para cruzar                                   |
| Info complementar governada (regra 8)                 | Sim               | Prazo de primeira resposta incluído por ser do mesmo chunk e diretamente relacionado ao SLA                                                                              |
| Observações condicionais                              | Não incluída      | Nenhuma divergência, limitação ou escalonamento necessário. O aviso sobre dados do cliente foi incorporado no corpo da resposta por ser contextual, não um alerta formal |

---

## Teste 3

### Pergunta

Quanto custa o frete para 600kg para Manaus?

### Resposta Produzida pelo Assistente

**Resposta:**

Não é possível informar o custo do frete com os dados disponíveis na documentação recuperada.

A documentação indica que cargas acima de 500kg se enquadram na regra de frete especial, cujo cálculo é: valor base × multiplicador regional. Como 600kg excede o limite de 500kg, essa regra se aplica (inferência aritmética). O multiplicador para a Região Norte é 1.8, e Manaus pertence à Região Norte por ser capital do estado do Amazonas (inferência geográfica — se a NovaTech utilizar regiões logísticas próprias que difiram das regiões geográficas do IBGE, esse enquadramento pode não estar correto).

Porém, o valor base necessário para completar o cálculo não consta na documentação recuperada. Sem ele, não é possível calcular o custo final.

Para obter o valor base atualizado, recomendo consultar a área Comercial.

**Fontes consultadas:**

- PROC-042-v2, seção 2

**Observações:**

- Informação parcial: a fórmula e o multiplicador regional estão documentados, mas o valor base está ausente.
- A fonte parece truncada (o texto do chunk termina abruptamente após listar a Região Centro-Oeste). Pode haver informação adicional no documento completo.
- A associação Manaus → Região Norte foi feita com base em geografia do IBGE. Validar se a NovaTech utiliza regiões logísticas distintas.

### Fontes Utilizadas

- PROC-042-v2, seção 2

### Chunks Utilizados

- Chunk C

### Guardrails Aplicados

| Guardrail                               | Aplicado? | Detalhe                                                                                                                                 |
| --------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Citou fonte                             | Sim       | PROC-042-v2, seção 2                                                                                                                    |
| Não inventou informação                 | Sim       | Não inventou valor base, não calculou preço fictício                                                                                    |
| Base nos chunks + limites de inferência | Sim       | Duas inferências usadas e explicitamente declaradas: aritmética (600 > 500) e geográfica (Manaus = Norte), ambas na lista de permitidas |
| Protocolo de ausência parcial           | Sim       | Informou o que tem (fórmula + multiplicador), identificou o que falta (valor base), direcionou para Comercial                           |
| Sinalização de inferência geográfica    | Sim       | Ressalva sobre regiões logísticas vs. geográficas conforme `<limites_de_inferencia>`                                                    |
| Chunk truncado sinalizado               | Sim       | Informou nas Observações que a fonte parece incompleta                                                                                  |
| Observações condicionais                | Sim       | Seção incluída por haver informação parcial, chunk truncado e inferência que requer validação                                           |

---

## Comparação V1 × V2

| Teste              | Aspecto                          | V1                                                                                   | V2                                                                                                            | Melhorou? |
| ------------------ | -------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | --------- |
| 1 — Carga perigosa | Tratamento da exceção            | Adotou uma interpretação implicitamente ("não se aplica") sem sinalizar alternativas | Apresentou as três interpretações possíveis sem escolher nenhuma, conforme regra 9                            | Sim       |
| 1 — Carga perigosa | Informação do procedimento geral | Omitiu procedimento geral (abrir chamado, fotos)                                     | Incluiu procedimento geral como contexto, sinalizando que pode não se aplicar ao caso                         | Sim       |
| 1 — Carga perigosa | Clareza sobre o que falta        | Disse que "não especifica prazo alternativo"                                         | Disse que não é possível determinar se é proibição, prazo diferente ou regulamentação externa                 | Sim       |
| 2 — SLA Gold       | Resposta principal               | Correta e completa                                                                   | Correta e completa (sem alteração substantiva)                                                                | Igual     |
| 2 — SLA Gold       | Dados do cliente                 | Não mencionou ausência de dados do sistema                                           | Sinalizou que não há dados do CRM para cruzar e sugeriu verificação                                           | Sim       |
| 2 — SLA Gold       | Formato                          | Seção "Observações" com "Nenhuma divergência" (ruído)                                | Seção "Observações" omitida por não haver alertas                                                             | Sim       |
| 3 — Frete Manaus   | Inferência geográfica            | Usou sem declarar (Manaus = Norte)                                                   | Declarou explicitamente a inferência e adicionou ressalva sobre regiões logísticas                            | Sim       |
| 3 — Frete Manaus   | Inferência aritmética            | Usou sem declarar (600 > 500)                                                        | Declarou explicitamente                                                                                       | Sim       |
| 3 — Frete Manaus   | Chunk truncado                   | Mencionou nas observações do documento de teste, mas o assistente não sinalizou      | Assistente sinalizou proativamente nas Observações                                                            | Sim       |
| 3 — Frete Manaus   | Clareza sobre o que falta        | "Não contém o valor base"                                                            | "Não contém o valor base" + direcionamento específico para Comercial + informação parcial claramente separada | Sim       |
| **Geral**          | Guardrails acionados             | 4 de 4 básicos                                                                       | 4 básicos + 6 novos guardrails testados                                                                       | Sim       |
| **Geral**          | Inferências implícitas           | 3 não declaradas nos 3 testes                                                        | 0 não declaradas                                                                                              | Sim       |
| **Geral**          | Formato condicional              | Observações sempre presentes (mesmo vazias)                                          | Observações apenas quando relevantes (Testes 1 e 3: presentes; Teste 2: omitida)                              | Sim       |
