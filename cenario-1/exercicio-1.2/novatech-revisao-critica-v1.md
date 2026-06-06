# NovaTech — Revisão Crítica do System Prompt V1

**Papel:** Principal Prompt Engineer / Principal AI Architect
**Objetivo:** Identificar falhas, riscos e oportunidades de melhoria
**Data:** Junho/2026
**Documento sob revisão:** System Prompt V1 + Resultados dos Testes 1, 2 e 3

---

## Parte 1 — Avaliação das Respostas dos Testes

---

### Teste 1 — Carga Perigosa

**1. A resposta estava correta?**
Parcialmente. A resposta afirma que cargas perigosas são "exceção à regra geral de devolução", o que é factualmente suportado pelo chunk. Porém, a formulação "essa regra não se aplica a cargas perigosas" é uma inferência razoável mas não trivial — o texto original diz "exceto cargas classificadas como perigosas", o que pode significar tanto "não podem ser devolvidas" quanto "possuem regra diferente". A resposta tratou como a segunda interpretação, mas não há base documental para escolher uma sobre a outra.

**2. A resposta estava completa?**
Não. A resposta identificou a lacuna (ausência de prazo alternativo), o que é positivo. Porém, não informou ao atendente o que a política efetivamente diz que o cliente DEVE fazer no caso geral (abrir chamado no portal, anexar fotos). Essa informação poderia ser útil mesmo no caso de carga perigosa — ou pelo menos o assistente deveria ter sinalizado que o procedimento padrão pode ou não se aplicar.

**3. A fonte foi citada corretamente?**
Sim — POL-001, seção 3.2.

**4. Houve risco de interpretação incorreta?**
Sim, alto. Um atendente pode ler "essa regra não se aplica" e concluir que a devolução é impossível, quando na realidade a política pode simplesmente ter um procedimento diferente não coberto por este chunk. O assistente não distinguiu entre "a documentação proíbe" e "a documentação não cobre este caso".

**5. Houve alguma inferência implícita?**
Sim. O assistente inferiu que "exceto" significa "não se aplica a regra de 7 dias". Essa é a leitura mais natural, mas o Prompt V1 não orienta o modelo sobre como tratar termos que criam exceção sem definir a regra alternativa. Outra inferência: o assistente recomendou escalonamento para "Operações ou Compliance" — essa escolha de áreas não está no chunk, foi inferida da estrutura do prompt (que menciona essas áreas no contexto estático). Não é uma invenção grave, mas é uma extrapolação.

**6. O comportamento é adequado para produção?**
Parcialmente. A cautela em não inventar um prazo é excelente. Porém, em um ambiente corporativo com 320 chamados/dia, uma resposta que diz "não sei, escalone" sem esgotar a informação parcial disponível gera carga desnecessária nos supervisores. O assistente deveria ter sido mais preciso sobre o que a documentação diz e o que ela não diz.

---

### Teste 2 — Cliente Gold

**1. A resposta estava correta?**
Sim. SLA de resolução de 24h para cliente Gold está explícito no Chunk B.

**2. A resposta estava completa?**
Sim para a pergunta feita. Porém, há um risco sutil: o assistente adicionou proativamente o prazo de primeira resposta (2h), que não foi perguntado. Isso é útil, mas levanta uma questão de design — o prompt não define se o assistente deve responder estritamente o que foi perguntado ou se deve agregar informação contextual do mesmo chunk.

**3. A fonte foi citada corretamente?**
Sim — SLA-2024. Porém, falta a seção ou cláusula específica. O Chunk B não fornece seção, então o assistente não tinha como citar com mais granularidade. Isso é uma limitação do chunk, não do prompt, mas o prompt deveria orientar o que fazer quando o chunk não traz seção/versão.

**4. Houve risco de interpretação incorreta?**
Baixo. A resposta é direta e o dado é inequívoco.

**5. Houve alguma inferência implícita?**
Sim, uma menor: a decisão de incluir o prazo de primeira resposta como informação complementar. Não é problemática, mas é uma escolha que o prompt não governa explicitamente.

**6. O comportamento é adequado para produção?**
Sim. Esta é a resposta mais limpa dos três testes. Porém, em produção, o assistente não saberá automaticamente que o cliente é Gold — essa informação veio na pergunta do atendente. Se o atendente informar a classificação errada, o assistente responderá com o SLA errado. O prompt não orienta o assistente a cruzar dados do cliente (contexto dinâmico `<dados_do_cliente>`) com a pergunta para detectar inconsistências.

---

### Teste 3 — Frete para Manaus

**1. A resposta estava correta?**
Sim, no que diz respeito à informação fornecida (multiplicador 1.8 para Região Norte).

**2. A resposta estava completa?**
Não, e por uma razão que vai além da ausência do valor base. O assistente assumiu que Manaus pertence à Região Norte. Isso é factualmente correto (Manaus é capital do Amazonas, Região Norte), mas o Chunk C não mapeia cidades a regiões — ele lista apenas regiões. O assistente fez uma inferência geográfica que está correta, mas que usa conhecimento externo ao chunk. Isso viola tecnicamente a regra 1 do prompt: "Responda SOMENTE com base nas informações presentes nos chunks."

**3. A fonte foi citada corretamente?**
Sim — PROC-042-v2, seção 2.

**4. Houve risco de interpretação incorreta?**
Médio. O atendente recebe uma resposta parcial com o multiplicador, mas sem o valor base não consegue calcular nada. Pode gerar frustração ("o assistente me deu uma fórmula que não consigo usar"). Além disso, se a NovaTech usar regiões logísticas próprias que não coincidam com as regiões geográficas do IBGE, a associação Manaus → Região Norte pode estar errada.

**5. Houve alguma inferência implícita?**
Sim, duas:

- Manaus = Região Norte (conhecimento geográfico externo ao chunk).
- 600kg > 500kg, portanto se enquadra na regra de frete especial (inferência lógica correta, mas não explicitada pelo assistente).

**6. O comportamento é adequado para produção?**
Parcialmente. O protocolo de ausência foi acionado, o que é positivo. Mas a resposta parcial sem utilidade prática (multiplicador sem valor base) pode treinar os atendentes a ignorar respostas parciais do assistente. Em produção, seria mais útil que o assistente dissesse claramente: "Não consigo calcular o valor do frete porque a documentação recuperada não contém o valor base. O multiplicador regional para a Região Norte é 1.8 (PROC-042-v2, seção 2), mas você precisará do valor base junto à área Comercial para concluir o cálculo."

---

## Parte 2 — Avaliação Crítica do Prompt V1

---

### Falhas de Prompt Engineering

**F1 — Ambiguidade no escopo de "SOMENTE com base nos chunks"**

A regra 1 diz "Responda SOMENTE com base nas informações presentes nos chunks." Mas o Teste 3 demonstrou que o modelo precisa usar conhecimento geral (Manaus pertence à Região Norte) para conectar a pergunta ao chunk. O prompt não define o limite entre "informação do chunk" e "conhecimento geral necessário para interpretar o chunk". Isso cria um espectro cinzento: associar Manaus ao Norte é aceitável? E associar um CEP a uma região? E inferir que "dias úteis" exclui finais de semana?

**F2 — Falta de instrução sobre informação complementar não solicitada**

O Teste 2 mostrou o assistente adicionando proativamente o prazo de primeira resposta quando só o SLA de resolução foi perguntado. O prompt não define se o assistente deve ser estritamente responsivo (responder apenas o que foi perguntado) ou contextualmente proativo (agregar informação relacionada do mesmo chunk). Ambas as abordagens têm trade-offs: a primeira é mais segura, a segunda é mais útil. Sem orientação, o modelo decide por conta — comportamento inconsistente entre respostas.

**F3 — Instrução "NUNCA invente" sem definição operacional de "inventar"**

O prompt repete "nunca invente" em dois blocos, mas não define a fronteira entre inventar e inferir. No Teste 3, dizer que Manaus está na Região Norte é invenção (informação não presente no chunk) ou inferência legítima (conhecimento básico necessário para operar)? Sem essa definição, o guardrail é forte na intenção mas fraco na execução.

**F4 — Regra de conflito entre documentos depende de metadado inexistente**

A regra 4 de `<regras>` e toda a lógica de `<prioridade_entre_fontes>` dependem de "data de vigência" dos documentos. Porém, os chunks de teste não contêm data de vigência. Se o pipeline RAG não injetar esse metadado consistentemente, o modelo não terá como aplicar a hierarquia temporal. A regra se torna letra morta.

**F5 — Redundância sem valor entre `<regras>` e `<ausencia_de_informacao>`**

A proibição de inventar aparece em ambos os blocos. Embora a justificativa no documento V1 seja mitigar Lost in the Middle, a formulação é quase idêntica nos dois blocos. Redundância eficaz deveria usar formulações complementares (uma dizendo o que NÃO fazer, outra dizendo o que fazer NO LUGAR), não repetição do mesmo conceito.

**F6 — Formato de resposta rígido para perguntas simples**

O bloco `<formato_de_resposta>` exige três seções (Resposta, Fontes, Observações) para toda resposta. Para o Teste 2 (pergunta direta com resposta direta), a seção "Observações" ficou com conteúdo genérico ("Nenhuma divergência encontrada"). Em produção com 192 consultas/dia ao assistente (60% de 320), forçar um formato tripartido para perguntas simples gera ruído visual. O prompt deveria permitir supressão de seções vazias.

---

### Falhas de Context Engineering

**C1 — Ausência de instrução sobre dados do cliente no contexto dinâmico**

O mapeamento de contexto prevê `<dados_do_cliente>` como componente dinâmico, mas o prompt V1 não contém nenhuma instrução sobre como usar esses dados. Se o pipeline injetar "Cliente: Transportes Iguaçu — Tier: Gold" no contexto, o modelo não sabe se deve: cruzar o tier do cliente com a tabela de SLA automaticamente, usar o dado para personalizar a resposta, ou simplesmente ignorar. Componente mapeado mas não governado.

**C2 — Orçamento de contexto não possui mecanismo de corte**

A estimativa de tokens prevê ~800–1.500 tokens para chunks e ~400–800 para histórico. Mas o prompt não orienta o orquestrador sobre o que cortar quando o orçamento estoura. Se uma conversa longa gerar 1.200 tokens de histórico e o RAG retornar 5 chunks de 300 tokens, o total dinâmico sobe para ~2.700 tokens — acima da estimativa. Quem perde? Chunks? Histórico? Nenhuma regra de degeneração graceful foi definida.

**C3 — Histórico de conversa sem delimitação de escopo**

O mapeamento prevê "até 3 turnos" de histórico, mas o prompt não instrui o modelo sobre como ponderar o histórico versus os chunks atuais. Se o turno anterior do assistente contiver informação de um chunk que não foi recuperado novamente neste turno, o modelo deve usar o dado do histórico (informação potencialmente desatualizada) ou ignorar (perda de contexto conversacional)?

**C4 — Lost in the Middle: a zona de risco contém a hierarquia de fontes**

O próprio documento V1 reconhece que a hierarquia de fontes (`<prioridade_entre_fontes>`) fica na zona intermediária do contexto. Essa é justamente a instrução mais importante quando há conflito entre documentos — o cenário mais perigoso do sistema. Colocar a lógica de resolução de conflitos na zona de menor atenção é um risco estrutural.

**C5 — Sem instrução para o modelo sobre chunks truncados**

O Teste 3 usou um Chunk C visivelmente truncado. Em produção, o pipeline de chunking pode gerar chunks cortados no meio de uma frase, tabela ou lista. O prompt não orienta o modelo sobre como tratar informação que parece incompleta — deve usar o que tem, deve sinalizar ao atendente, deve descartar?

---

### Riscos Operacionais

**O1 — Documentos sem data de vigência tornam a hierarquia inaplicável**

O Chunk B (SLA-2024) tem um ano no nome. O Chunk A (POL-001) e o Chunk C (PROC-042-v2) têm versão mas não data. Se dois documentos conflitarem e nenhum tiver data de vigência, o modelo não tem critério objetivo para escolher. A hierarquia por tipo de documento (POL > PROC > SLA) resolve parcialmente, mas conflitos dentro da mesma categoria ficam sem critério.

**O2 — 3 áreas atualizando documentos sem processo unificado = conflitos inevitáveis**

O cenário da NovaTech informa que Operações, Compliance e Comercial atualizam documentos independentemente. O prompt V1 trata conflitos como exceção ("Se dois ou mais chunks apresentarem informações contraditórias..."), mas na operação real isso será regra, não exceção. O prompt subestima a frequência do cenário.

**O3 — Citação de fonte sem URL ou link navegável**

O formato de citação ("POL-001, seção 3.2") exige que o atendente saiba onde encontrar esse documento nas três fontes (SharePoint, Confluence, pasta de rede). Em produção, o atendente pode não saber localizar "PROC-042-v2" sem um link direto. O prompt deveria orientar a inclusão do repositório de origem, ou o pipeline deveria injetar o link como metadado do chunk.

**O4 — Recuperação de chunks irrelevantes não é tratada**

O bloco `<uso_dos_chunks>` diz "utilize apenas chunks cuja informação seja diretamente relevante", mas não define "diretamente relevante" nem orienta o modelo sobre o que fazer com chunks recuperados que claramente não se aplicam à pergunta. O modelo deve ignorar silenciosamente? Deve mencionar que descartou chunks? Em produção, se o RAG retornar 5 chunks dos quais 3 são irrelevantes, o modelo pode tentar forçar relevância onde não há.

---

### Riscos de Alucinação

**H1 — Inferência geográfica e lógica como porta de entrada**

O Teste 3 demonstrou que o modelo usou conhecimento externo (Manaus = Norte) para conectar a pergunta ao chunk. Esse tipo de "micro-inferência" é uma superfície de alucinação: se o modelo pode associar cidades a regiões, ele pode começar a associar tipos de carga a classificações, prazos a calendários, ou valores a faixas. Cada inferência parece pequena, mas cumulativamente degradam a confiabilidade.

**H2 — Pressão para ser útil pode superar o guardrail de ausência**

O prompt enfatiza "NUNCA invente" mas não contrabalança com uma instrução positiva de que é valioso e esperado dizer "não sei". Modelos de linguagem têm viés de prestatividade — a pressão interna para fornecer uma resposta útil pode, em cenários limítrofes, levar o modelo a "esticar" um chunk para cobrir algo que ele não cobre de fato. Exemplo: se perguntarem sobre devolução de carga perecível e o chunk só mencionar carga perigosa, o modelo pode generalizar a exceção.

**H3 — Formato de resposta estruturado pode mascarar incerteza**

O formato com seções (Resposta / Fontes / Observações) transmite autoridade e confiança. Uma resposta parcial formatada assim pode parecer mais completa do que é. No Teste 3, a resposta formatada com fonte citada e observações parece completa e confiável, mas na prática não responde à pergunta ("quanto custa?"). O formato pode criar uma falsa sensação de que a pergunta foi respondida.

**H4 — Ausência de instrução sobre negações**

Se o atendente perguntar "É verdade que o prazo de devolução é de 15 dias?", o modelo precisa negar afirmativamente com base no chunk (que diz 7 dias úteis). Mas o prompt não instrui o modelo sobre como corrigir premissas falsas do atendente. O modelo pode simplesmente responder "o prazo é de 7 dias úteis" sem explicitar que a premissa de 15 dias está incorreta — o atendente pode não perceber a correção implícita.

---

## Parte 3 — Revisão Especial dos Casos de Teste

---

### Caso 1 — Carga Perigosa

**O texto da política é inequívoco?**

Não. "Mercadorias podem ser devolvidas em até 7 dias úteis (...) exceto cargas classificadas como perigosas" admite pelo menos três leituras:

- Leitura A: Cargas perigosas não podem ser devolvidas em nenhuma circunstância.
- Leitura B: Cargas perigosas podem ser devolvidas, mas com prazo ou procedimento diferente (não especificado aqui).
- Leitura C: Cargas perigosas seguem regulamentação específica da ANTT, que prevalece sobre a política interna.

O assistente adotou a Leitura B implicitamente ("a política não especifica um prazo alternativo"), mas não informou ao atendente que existem outras interpretações possíveis. Em um ambiente corporativo, a ambiguidade deveria ter sido sinalizada com mais clareza.

**O prompt deveria orientar melhor o tratamento de exceções?**

Sim. O Prompt V1 não contém nenhuma instrução sobre como tratar cláusulas de exceção em documentos. Termos como "exceto", "salvo", "não se aplica a" criam zonas de ambiguidade que o modelo precisa de orientação explícita para navegar. Uma instrução dedicada reduziria a variância de comportamento nesses casos.

---

### Caso 2 — Cliente Gold

**Existe risco de excesso de informação?**

Risco baixo neste caso específico, mas o padrão é preocupante. O assistente adicionou o prazo de primeira resposta sem que tenha sido perguntado. Em cenários com chunks maiores, esse comportamento proativo pode resultar em respostas longas que diluem a informação principal. Para 192 consultas/dia, respostas concisas e focadas têm mais valor operacional do que respostas abrangentes.

**Existe risco de inconsistência entre dados do cliente e a pergunta?**

Sim, e este é o risco mais relevante deste caso. Se o pipeline injetar `<dados_do_cliente>Tier: Silver</dados_do_cliente>` mas o atendente disser "meu cliente é Gold", o assistente precisa de orientação sobre qual fonte de verdade utilizar. O Prompt V1 não cobre esse cenário.

---

### Caso 3 — Frete para Manaus

**O protocolo de ausência foi suficiente?**

Funcionou para o cenário simples (um dado faltante), mas é frágil para cenários compostos. Considere: se o RAG retornar o Chunk C com multiplicadores regionais e um segundo chunk com uma tabela de valores base, mas a tabela contiver valores para "Frete Padrão" e "Frete Expresso" sem indicar qual se aplica a 600kg — o modelo precisaria escolher entre dois valores base, e o prompt não orienta essa escolha. O protocolo de ausência trata o caso binário (tem/não tem informação) mas não o caso de informação ambígua ou insuficientemente específica.

**Cenário de valores conflitantes:**

Se um chunk trouxer "valor base R$ 2,50/kg para cargas > 500kg" (de 2023) e outro trouxer "valor base R$ 3,10/kg para cargas > 500kg" (de 2024), o prompt orienta usar o mais recente. Mas se nenhum tiver data? Se ambos forem PROC-042 mas versões diferentes (v1 e v2) sem indicação de qual está vigente? O modelo ficaria sem critério objetivo e o guardrail de "priorize o mais recente" seria inaplicável.

---

## Parte 4 — Síntese

---

### Pontos Fortes do Prompt V1

1. A estrutura em blocos XML com tags semânticas é sólida e facilita manutenção.
2. Os guardrails anti-alucinação ("nunca invente") demonstraram eficácia nos três testes — o modelo não inventou informação em nenhum caso.
3. O protocolo de ausência de informação funcionou nos dois casos em que foi necessário (Testes 1 e 3).
4. A hierarquia de fontes é um diferencial — poucos prompts de produção definem prioridade entre tipos de documento.
5. O formato de resposta é consistente e auditável.
6. A separação entre contexto estático e dinâmico é bem definida e facilita a implementação do pipeline.

---

### Pontos Fracos do Prompt V1

1. Não define a fronteira entre inferência legítima e invenção.
2. Não governa o uso do componente dinâmico `<dados_do_cliente>`.
3. Não trata chunks truncados ou incompletos.
4. Hierarquia temporal depende de metadado que pode não existir.
5. Formato rígido mesmo para perguntas simples.
6. Não trata cláusulas de exceção em documentos.
7. Não define comportamento para correção de premissas falsas do atendente.

---

### Melhorias Recomendadas

| #   | Problema identificado                                      | Impacto                                                                                                                                                                                              | Severidade | Recomendação                                                                                                                                                                                                                                                                   |
| --- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| M1  | Fronteira entre inferência e invenção indefinida (F1, F3)  | Modelo pode usar conhecimento externo sem controle, ou ser excessivamente restritivo e inútil. Compromete a confiabilidade de toda resposta que exija qualquer interpretação.                        | **Alta**   | Criar uma seção `<limites_de_inferencia>` que defina explicitamente o que é permitido (ex: associar cidades a estados/regiões, converter unidades, interpretar abreviações) e o que é proibido (ex: assumir prazos, valores, procedimentos não documentados).                  |
| M2  | `<dados_do_cliente>` mapeado mas não governado (C1)        | Se o pipeline injetar dados do cliente sem instrução de uso, o modelo ignora ou usa de forma inconsistente. Risco de responder com SLA errado se atendente informar tier diferente do cadastrado.    | **Alta**   | Adicionar bloco `<uso_dados_cliente>` com instrução de cruzamento: se houver divergência entre o que o atendente informa e o que o contexto mostra, sinalizar a discrepância.                                                                                                  |
| M3  | Hierarquia temporal sem metadado (F4, O1)                  | Regra de "priorizar documento mais recente" é inaplicável se os chunks não contiverem data. A resolução de conflitos fica sem critério objetivo.                                                     | **Alta**   | Exigir que o pipeline RAG injete data_vigência como metadado obrigatório de cada chunk. No prompt, adicionar fallback: "Se a data de vigência não estiver disponível, sinalize a divergência e recomende escalonamento."                                                       |
| M4  | Tratamento de exceções documentais ausente (Caso 1)        | Termos como "exceto" e "salvo" criam ambiguidade que o modelo resolve por conta. Risco de interpretação incorreta em políticas com cláusulas de exceção.                                             | **Alta**   | Adicionar instrução em `<regras>`: "Quando o texto documental contiver exceções sem definição do procedimento alternativo, informe a exceção e explicite que o procedimento aplicável não consta na documentação disponível. Não assuma nenhuma das interpretações possíveis." |
| M5  | Chunks truncados sem tratamento (C5)                       | Modelo pode usar informação incompleta como se fosse completa, ou descartar chunk inteiro que continha informação parcialmente útil.                                                                 | **Média**  | Adicionar instrução em `<uso_dos_chunks>`: "Se um chunk parecer truncado ou incompleto (frase cortada, tabela sem todas as linhas, lista interrompida), utilize a informação disponível e sinalize na seção Observações que a fonte pode estar incompleta."                    |
| M6  | Formato rígido para respostas simples (F6)                 | Seções vazias ("Nenhuma divergência") geram ruído visual em 192 consultas/dia. Atendentes podem parar de ler a seção Observações por habituação.                                                     | **Média**  | Tornar a seção "Observações" condicional: "Inclua a seção Observações apenas quando houver divergências, limitações ou recomendação de escalonamento. Omita quando não houver nada a reportar."                                                                                |
| M7  | Informação complementar não solicitada sem governança (F2) | Comportamento inconsistente: às vezes o modelo agrega informação do mesmo chunk, às vezes não. Sem regra, depende do "humor" do modelo.                                                              | **Média**  | Definir regra: "Ao responder, inclua informação complementar do mesmo chunk apenas se for diretamente relacionada à pergunta e puder afetar o atendimento ao cliente. Não agregue informações de outros chunks não solicitadas."                                               |
| M8  | Orçamento de contexto sem regra de degeneração (C2)        | Se o contexto exceder o limite, não há definição de o que cortar. Risco de perder chunks ou histórico arbitrariamente.                                                                               | **Média**  | Definir prioridade de corte no pipeline: (1) manter todos os chunks, (2) sumarizar histórico além de 2 turnos, (3) comprimir metadados. Documentar como instrução para o orquestrador, não para o modelo.                                                                      |
| M9  | Citação sem localização navegável (O3)                     | Atendente recebe "POL-001, seção 3.2" mas não sabe onde encontrar o documento. Reduz a utilidade da citação em ambiente de produção.                                                                 | **Média**  | Exigir que o pipeline RAG injete repositório de origem (SharePoint, Confluence, pasta de rede) como metadado. Ajustar formato de citação: "POL-001, seção 3.2 — SharePoint/Políticas".                                                                                         |
| M10 | Correção de premissas falsas não instruída (H4)            | Se o atendente afirmar algo incorreto ("o prazo é 15 dias, certo?"), o modelo pode responder com o dado correto sem explicitar que a premissa está errada. O atendente pode não perceber a correção. | **Baixa**  | Adicionar instrução: "Se a pergunta do atendente contiver uma afirmação factualmente incorreta segundo a documentação, corrija a premissa explicitamente antes de fornecer a resposta."                                                                                        |
| M11 | Sem instrução sobre negações e confirmações (H4)           | Modelo não distingue entre "qual é o prazo?" (pergunta aberta) e "é verdade que o prazo é X?" (pedido de confirmação). O segundo exige validação explícita.                                          | **Baixa**  | Incluir em `<regras>`: "Se o atendente pedir confirmação de um dado específico, confirme ou corrija explicitamente com base na documentação, citando a fonte."                                                                                                                 |
| M12 | Pressão de prestatividade não contrabalanceada (H2)        | Guardrail diz "nunca invente" mas não reforça que dizer "não sei" é valioso. Em cenários limítrofes o modelo pode esticar interpretações.                                                            | **Baixa**  | Adicionar frase em `<regras>`: "Informar que a documentação não cobre um assunto é uma resposta válida e preferível a qualquer extrapolação."                                                                                                                                  |
