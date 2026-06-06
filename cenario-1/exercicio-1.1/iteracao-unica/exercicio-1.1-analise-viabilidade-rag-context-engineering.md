# Análise de Viabilidade Técnica — Assistente Corporativo RAG

## NovaTech Logística | Preparado por DB1

---

## 1. Resumo Executivo

A NovaTech busca construir um assistente corporativo baseado em RAG para reduzir o tempo médio de consulta a documentação de 12 para menos de 2 minutos por chamado, atendendo 45 operadores em ~192 consultas/dia (60% de 320 chamados).

A base de conhecimento totaliza aproximadamente **5,7 milhões de palavras (~7,6 milhões de tokens)**, distribuídas entre PDFs do SharePoint (800 documentos), wiki Confluence (400 páginas) e planilhas Excel (50 arquivos). As fontes apresentam heterogeneidade significativa: tabelas com 15+ colunas, documentos escaneados (OCR), macros Confluence, fórmulas interdependentes em Excel e — criticamente — contradições entre versões de documentos sem governança unificada.

**Viabilidade geral: MÉDIA**, condicionada a investimento robusto em pipeline de ingestão, governança documental e estratégia de context engineering. O projeto é tecnicamente realizável, mas o prazo de 3 meses é agressivo considerando a complexidade das fontes e a necessidade de tratamento especial para tabelas, OCR e resolução de conflitos entre documentos. Recomenda-se um escopo faseado com go-live inicial sobre o subconjunto de documentos mais limpos (PDFs textuais e wiki), expandindo para fontes complexas em iterações subsequentes.

---

## 2. Análise das Fontes

### 2.1 Tabela Comparativa

| Critério                          | PDFs Textuais (SharePoint)                                                                                                                                                           | PDFs Escaneados                                                                                                                         | Wiki Confluence                                                                                                                                              | Planilhas Excel                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Volume estimado**               | ~560 docs (70% de 800)                                                                                                                                                               | ~240 docs (30% de 800)                                                                                                                  | 400 páginas                                                                                                                                                  | 50 arquivos                                                                                                                                          |
| **Desafios de ingestão**          | Tabelas complexas com 15+ colunas perdem estrutura na extração; fluxogramas como imagens não são extraíveis como texto                                                               | Qualidade do OCR depende da resolução do scan; documentos com carimbos, assinaturas e marcas d'água degradam a extração                 | Macros customizadas podem gerar conteúdo dinâmico não capturável por API; links internos criam dependências entre páginas                                    | Fórmulas interdependentes entre abas; o "significado" de uma célula depende de cabeçalhos, contexto de linha/coluna e outras abas                    |
| **Desafios de chunking**          | Tabelas não podem ser quebradas arbitrariamente; uma tabela de frete com 15 colunas, se dividida, perde coerência semântica                                                          | Erros de OCR criam ruído que degrada embeddings; layout multi-coluna pode embaralhar a ordem de leitura                                 | Páginas com muitos links internos perdem contexto quando isoladas; conteúdo gerado por macros pode estar ausente                                             | Estrutura tabular não se adapta a chunking textual linear; relações entre abas criam dependências que chunks isolados não capturam                   |
| **Desafios de retrieval**         | Consultas sobre valores específicos em tabelas (ex: "qual o SLA para cliente tipo B na rota X?") exigem matching preciso que busca vetorial pura não resolve bem                     | Erros de OCR reduzem a similaridade semântica com a query; termos técnicos podem ser mal reconhecidos                                   | Respostas completas podem exigir informações de múltiplas páginas conectadas por links                                                                       | Queries sobre cálculos (ex: "como é calculado o frete para carga fracionada?") exigem entender fórmulas, não apenas valores                          |
| **Impacto na qualidade**          | ALTO — tabelas de SLA e frete são consultas frequentes; se mal indexadas, o assistente falha nos casos mais comuns                                                                   | MÉDIO-ALTO — erros de OCR geram respostas incorretas silenciosamente (o modelo não sabe que o texto-fonte está errado)                  | MÉDIO — conteúdo textual é o mais adequado para RAG, mas macros e links criam lacunas                                                                        | MÉDIO — planilhas são fontes de referência atualizadas mensalmente; se desatualizadas no índice, geram respostas erradas                             |
| **Estratégias de mitigação**      | Extração especializada de tabelas (Camelot, Tabula, Azure Document Intelligence); representação de tabelas como markdown ou JSON; indexação separada de tabelas inteiras como chunks | Azure Document Intelligence com modelo prebuilt-layout; validação humana de amostra; pré-processamento de imagens (deskew, binarização) | API REST do Confluence para extração estruturada; expansão de macros onde possível; resolução de links na fase de ingestão adicionando contexto referenciado | Conversão para formato textual descritivo ("Na aba X, para a coluna Y, quando Z..."); pré-cálculo de valores; snapshot mensal dos valores resolvidos |
| **Complexidade de implementação** | MÉDIA-ALTA                                                                                                                                                                           | ALTA                                                                                                                                    | MÉDIA                                                                                                                                                        | ALTA                                                                                                                                                 |
| **Risco residual**                | Tabelas muito complexas ainda podem ser mal interpretadas; fluxogramas como imagens permanecem inacessíveis                                                                          | OCR nunca será 100% preciso; documentos com qualidade de scan ruim serão fontes permanentes de erro                                     | Macros complexas podem gerar conteúdo invisível ao pipeline                                                                                                  | Fórmulas com dependências circulares ou condicionais complexas podem ser inviáveis de converter para texto                                           |

### 2.2 Análise Detalhada por Fonte

**PDFs Textuais do SharePoint.** Esta é simultaneamente a maior fonte e a mais desafiadora. O problema central não é o volume, mas a natureza dos dados: tabelas de frete com 15+ colunas são precisamente o tipo de conteúdo que atendentes mais consultam, e precisamente o tipo que extração padrão de PDF mais distorce. Um PDF parser convencional (PyPDF2, pdfplumber) tende a linearizar tabelas, transformando uma estrutura bidimensional em texto sequencial que perde a associação entre cabeçalho e valor. Quando o modelo recebe "São Paulo | Rio de Janeiro | 3 dias | R$ 45,00 | 2 dias | R$ 72,00" sem estrutura, ele não consegue responder "qual o prazo para SP-RJ no SLA Premium?" com confiança.

A mitigação exige extração tabular especializada. Azure Document Intelligence (prebuilt-layout) é a opção natural dado que a NovaTech já tem licenças Azure, e oferece extração estruturada de tabelas com coordenadas de célula. A alternativa open-source (Camelot + Tabula) funciona para tabelas com linhas visíveis, mas falha em tabelas sem bordas. Cada tabela extraída deve ser representada como chunk independente em formato markdown ou JSON, com metadados indicando documento de origem, página e data de última atualização.

Fluxogramas embutidos como imagens representam um desafio à parte. Se contêm texto relevante para decisões operacionais, podem ser processados com OCR de imagem (Azure Computer Vision) ou modelos multimodais. Porém, a complexidade de interpretar fluxogramas programaticamente é alta e o ROI é questionável. Recomenda-se que, na primeira fase, fluxogramas sejam indexados apenas por seus metadados (título do documento, seção, descrição manual se disponível) e que respostas sobre processos que dependem de fluxogramas direcionem o atendente ao documento original.

**PDFs Escaneados.** Representando estimados 30% do acervo do SharePoint (~240 documentos), os PDFs escaneados introduzem uma camada adicional de incerteza. A qualidade do OCR depende diretamente da qualidade do scan original, que em ambientes corporativos varia enormamente: documentos escaneados em impressoras multifuncionais com alimentador automático frequentemente apresentam rotação, distorção, baixa resolução e artefatos.

O pipeline recomendado é: pré-processamento de imagem (deskew com OpenCV, binarização adaptativa, remoção de ruído) seguido de OCR via Azure Document Intelligence (que supera Tesseract em documentos corporativos, especialmente em português). Mesmo com esse pipeline, a taxa de erro estimada é de 2-5% por caractere em documentos de boa qualidade, podendo chegar a 10-15% em documentos degradados.

O risco crítico aqui é o erro silencioso: o modelo receberá texto com erros de OCR e gerará respostas com confiança, sem indicação de que a fonte está corrompida. Mitigação: adicionar score de confiança do OCR como metadado de cada chunk, e instruir o modelo via system prompt a sinalizar incerteza quando a confiança do OCR for baixa. Adicionalmente, uma amostra de ~10% dos documentos deve ser validada manualmente para calibrar expectativas de qualidade.

**Wiki Confluence.** Das quatro fontes, a wiki é a mais adequada para RAG: conteúdo textual nativo, estruturado em páginas com títulos e seções, e acessível via API REST. Os desafios são menores mas não triviais. Macros customizadas (jira-issues, roadmap, status, expand) podem gerar conteúdo que a API não retorna no corpo da página. Links internos entre páginas significam que uma resposta completa pode exigir informação de 2-3 páginas conectadas.

A estratégia recomendada é extrair via API REST do Confluence (endpoint /rest/api/content com expand=body.storage), processar o HTML retornado para texto limpo, resolver links internos adicionando contexto resumido da página referenciada como metadado, e lidar com macros conhecidas (expandindo as que têm conteúdo estático, marcando as dinâmicas como "conteúdo não disponível no índice").

**Planilhas Excel.** A dificuldade fundamental das planilhas é que são estruturas de dados, não documentos textuais. Uma célula com a fórmula `=VLOOKUP(B2, Tarifas!A:F, 5, FALSE)` contém significado semântico rico ("busque a tarifa correspondente na tabela de tarifas"), mas esse significado é implícito na estrutura, não no texto.

A abordagem recomendada é dupla: para planilhas de referência (tabelas de valores), converter para formato tabular markdown e indexar como chunks estruturados, similar às tabelas de PDF. Para planilhas com lógica de cálculo, criar descrições textuais manuais ou semi-automatizadas das regras de negócio que as fórmulas implementam. Esta segunda parte exige envolvimento das áreas de negócio e representa trabalho manual significativo.

A atualização mensal das planilhas exige que o pipeline de re-ingestão seja automatizado, com detecção de alterações e re-indexação incremental.

---

## 3. Estimativa de Volume

### 3.1 Premissas Explícitas

Para PDFs textuais, utilizo a premissa de **500 palavras por página**. Justificativa: documentos corporativos de logística com tabelas, cabeçalhos, espaçamento e elementos visuais têm densidade textual menor que documentos puramente textuais (onde 600-800 palavras/página seria razoável). A presença de tabelas com muitas colunas mas pouco texto por célula, fluxogramas ocupando espaço e formatação corporativa com margens generosas sustenta essa estimativa. Faixa realista: 350-650 palavras/página.

Para planilhas, utilizo a premissa de **5.000 palavras por planilha quando convertida para texto**. Justificativa: uma planilha corporativa típica com 3-5 abas, cada uma com 20-50 linhas e 8-15 colunas, gera ao ser linearizada em formato descritivo aproximadamente 3.000-7.000 palavras dependendo da complexidade. Adoto 5.000 como ponto médio.

### 3.2 Cálculos

**PDFs (SharePoint) — 800 documentos:**

- 800 PDFs × 10 páginas/PDF = 8.000 páginas
- 8.000 páginas × 500 palavras/página = **4.000.000 palavras**
- Faixa: 2.800.000 (350 pal/pág) a 5.200.000 (650 pal/pág)

**Wiki Confluence — 400 páginas:**

- 400 páginas × 1.500 palavras/página = **600.000 palavras**
- Faixa: 480.000 (assumindo ~20% de macros não extraíveis) a 660.000 (assumindo conteúdo expandido de links)

**Planilhas Excel — 50 arquivos:**

- 50 planilhas × 5.000 palavras/planilha = **250.000 palavras**
- Faixa: 150.000 (planilhas simples) a 350.000 (planilhas complexas)

### 3.3 Totais

| Métrica                      | Mínimo    | Estimativa Central | Máximo    |
| ---------------------------- | --------- | ------------------ | --------- |
| **Total de palavras**        | 3.430.000 | **4.850.000**      | 6.210.000 |
| **Total de tokens** (÷ 0,75) | 4.573.333 | **6.466.667**      | 8.280.000 |

**Nota sobre a conversão palavras→tokens:** O fator de 0,75 palavras/token (ou ~1,33 tokens/palavra) é uma aproximação razoável para inglês. Para português, a relação tende a ser ligeiramente pior (~1,4-1,5 tokens/palavra) devido a palavras mais longas, acentuação e conjugações verbais. Adotando 1,45 tokens/palavra como fator corrigido para português:

| Métrica                               | Mínimo    | Estimativa Central | Máximo    |
| ------------------------------------- | --------- | ------------------ | --------- |
| **Total de tokens (pt-BR corrigido)** | 4.973.500 | **7.032.500**      | 9.004.500 |

### 3.4 Impactos para Indexação Vetorial

Com ~7 milhões de tokens no corpus e chunks médios de 500 tokens, temos aproximadamente **14.000 chunks** na estimativa central. Considerações:

- **Armazenamento de embeddings:** 14.000 vetores × 1.536 dimensões (ada-002) × 4 bytes = ~86 MB. Trivial em termos de armazenamento.
- **Custo de embedding:** 7M tokens × $0,0001/1K tokens (ada-002) ≈ $0,70. Desprezível, mesmo com re-indexações mensais.
- **Latência de busca:** Com 14.000 vetores, busca ANN (approximate nearest neighbor) via Azure AI Search é sub-segundo mesmo sem otimização.
- **Custo de inferência:** O custo real está na chamada ao GPT-4o por consulta: ~192 consultas/dia × ~4.000 tokens médios por chamada (contexto + resposta) × $5/1M tokens (input GPT-4o) ≈ $3,84/dia ≈ **$115/mês**. Gerenciável.

O volume total do corpus **não é um gargalo**. O desafio real está na qualidade da ingestão e no orçamento de contexto por consulta, discutido a seguir.

---

## 4. Context Engineering e Orçamento de Contexto

Este é o capítulo mais crítico da análise. A qualidade do assistente será determinada não pelo volume da base, mas pela qualidade do contexto entregue ao modelo em cada consulta individual.

### 4.1 Orçamento de Contexto (GPT-4o, 128K tokens)

**Capacidade teórica máxima de chunks:**

- Janela total: 128.000 tokens
- System prompt + instruções: 2.000 tokens
- Disponível: 126.000 tokens
- Chunks de 500 tokens: 126.000 ÷ 500 = **252 chunks teóricos**

**Por que a capacidade teórica não deve ser utilizada:**

O cálculo de 252 chunks é enganoso e perigosamente otimista por quatro razões:

**Razão 1 — Reserva para resposta.** O modelo precisa de tokens para gerar a resposta. Uma resposta detalhada com citação de fontes consome 500-1.500 tokens. Reserva recomendada: **2.000 tokens**.

**Razão 2 — Reserva para histórico.** Em uma conversa multi-turno (o atendente faz perguntas de acompanhamento), o histórico cresce. Para 3-5 turnos de conversa, reservar **3.000-5.000 tokens**.

**Razão 3 — Efeito "Lost in the Middle".** Pesquisa demonstra que LLMs prestam mais atenção ao início e ao final do contexto, com degradação significativa no meio. Em testes com GPT-4 e Claude, a acurácia de recuperação de informação cai de ~90% nas posições iniciais e finais para ~50-60% nas posições centrais. Isso significa que adicionar mais chunks além de um ponto ótimo não apenas não ajuda — piora ativamente a qualidade, porque os chunks relevantes competem com chunks irrelevantes pela atenção do modelo, e podem acabar "enterrados" no meio do contexto.

**Razão 4 — Competição por atenção (Attention Budget).** O contexto do modelo é um recurso finito onde múltiplos elementos competem:

| Componente                                                         | Tokens Estimados | Prioridade  |
| ------------------------------------------------------------------ | ---------------- | ----------- |
| System prompt (identidade, regras, formato de resposta)            | 1.000            | Crítica     |
| Instruções de RAG (como citar fontes, como lidar com contradições) | 1.000            | Crítica     |
| Histórico de conversa (3-5 turnos)                                 | 3.000-5.000      | Alta        |
| Chunks recuperados (o contexto RAG propriamente dito)              | **variável**     | Alta        |
| Reserva para resposta                                              | 2.000            | Obrigatória |

### 4.2 Orçamento Prático Recomendado

| Componente                 | Tokens Alocados   |
| -------------------------- | ----------------- |
| System prompt + instruções | 2.000             |
| Histórico de conversa      | 4.000             |
| **Contexto RAG (chunks)**  | **6.000-10.000**  |
| Reserva para resposta      | 2.000             |
| **Total utilizado**        | **14.000-18.000** |

Com 6.000-10.000 tokens para contexto RAG e chunks de 500 tokens: **12 a 20 chunks por consulta**.

Note que estamos usando apenas **11-14% da janela de 128K tokens**. Isso é intencional. O objetivo não é preencher a janela, mas maximizar a relação sinal/ruído no contexto. 20 chunks altamente relevantes produzem respostas melhores que 200 chunks onde apenas 5 são relevantes — porque nos 200 chunks, o modelo precisa "encontrar a agulha no palheiro" e o efeito Lost in the Middle garante que muitas agulhas serão ignoradas.

### 4.3 Posicionamento Estratégico dos Chunks

Para mitigar o efeito Lost in the Middle, os chunks recuperados devem ser ordenados por relevância nas posições de maior atenção:

1. **Posição 1-3 (início do contexto RAG):** Chunks com maior score de relevância
2. **Posição central:** Chunks de suporte, contexto adicional
3. **Últimas posições (fim do contexto RAG):** Segundo e terceiro chunks mais relevantes (recency bias do modelo)

Essa estratégia "sanduíche" coloca o conteúdo mais importante nas extremidades e o conteúdo de suporte no meio.

### 4.4 Implicação para a Arquitetura

A limitação prática de 12-20 chunks por consulta impõe exigências severas na qualidade do retrieval:

- Cada chunk desperdiçado (irrelevante ou redundante) é um slot perdido.
- Re-ranking é obrigatório, não opcional — a diferença entre os top-20 e os top-50 resultados da busca vetorial determina a qualidade da resposta.
- Chunks devem ser auto-contidos (compreensíveis sem contexto externo) para que cada slot maximize seu valor informacional.
- Metadata filtering pré-retrieval (filtrar por categoria de documento, data, área) pode reduzir drasticamente o espaço de busca e melhorar a precisão.

---

## 5. Estratégia de Chunking

### 5.1 PDFs Textuais

**Estratégia: chunking semântico-estrutural com preservação de tabelas.**

Para o corpo textual dos PDFs, utilizar chunking semântico baseado em seções do documento (títulos, subtítulos), com tamanho alvo de **400-600 tokens** e overlap de **50-100 tokens** (10-20%). O overlap preserva continuidade semântica entre chunks adjacentes. O chunking respeita limites de parágrafo e seção — nunca quebra no meio de uma frase.

Para tabelas, a estratégia é fundamentalmente diferente. Cada tabela deve ser tratada como um chunk atômico. Uma tabela de frete com 15 colunas e 20 linhas pode gerar um chunk de 800-1.200 tokens. Isso excede o tamanho padrão, mas é preferível a fragmentar a tabela e perder a associação coluna-valor. Se a tabela for muito grande (>1.500 tokens), segmentar por blocos lógicos de linhas (ex: por região, por tipo de cliente) mantendo sempre os cabeçalhos em cada chunk.

Formato de representação de tabelas: markdown table é preferível a texto linearizado porque preserva a estrutura bidimensional de forma que o LLM pode interpretar. Exemplo:

```
| Origem | Destino | SLA Standard | SLA Premium | Valor Standard | Valor Premium |
|--------|---------|-------------|-------------|----------------|---------------|
| SP     | RJ      | 3 dias      | 1 dia       | R$ 45,00       | R$ 120,00     |
```

**Metadados por chunk:**

- Documento de origem (nome, path no SharePoint)
- Página(s) do PDF
- Seção/título hierárquico (ex: "Manual de Frete > Tabela Regional > Sul")
- Data de última modificação
- Tipo de conteúdo (texto, tabela, lista)
- Área responsável (Operações, Compliance, Comercial)

### 5.2 PDFs com Tabelas Complexas

**Estratégia: extração dual com indexação hierárquica (parent-child).**

Para documentos com tabelas de 15+ colunas, a extração via Azure Document Intelligence (prebuilt-layout) produz coordenadas de célula que permitem reconstruir a tabela fielmente. A estratégia parent-child funciona assim:

- **Parent chunk:** Seção completa do documento contendo a tabela, com contexto textual ao redor (título, notas de rodapé, observações). Tamanho: 1.000-2.000 tokens.
- **Child chunks:** A tabela segmentada em blocos lógicos (5-10 linhas cada, sempre com cabeçalhos). Tamanho: 300-600 tokens cada.

Na busca, os child chunks são indexados e recuperados. Quando um child é selecionado, o parent correspondente é incluído no contexto para fornecer o contexto explicativo necessário. Isso permite retrieval granular (encontrar a linha específica da tabela) sem perder o contexto semântico.

### 5.3 PDFs Escaneados

**Estratégia: OCR com validação + chunking conservador.**

Após OCR via Azure Document Intelligence, o texto extraído passa por limpeza (remoção de artefatos, correção de quebras de linha espúrias, normalização de espaçamento). O chunking segue a mesma estratégia dos PDFs textuais, mas com duas diferenças:

- **Chunks menores (300-400 tokens):** Texto com erros de OCR gera embeddings de menor qualidade. Chunks menores reduzem a probabilidade de ruído excessivo por chunk.
- **Metadado de confiança do OCR:** Cada chunk recebe um score de confiança médio baseado nos scores de confiança por palavra do OCR. Chunks com confiança abaixo de 80% recebem flag para revisão humana.

### 5.4 Wiki Confluence

**Estratégia: chunking estrutural baseado em seções da página.**

A wiki é a fonte mais RAG-friendly. Cada página do Confluence tem estrutura de headings (H1-H6) que fornece limites naturais de chunk. A estratégia:

- Cada seção (H2 ou H3) se torna um chunk, com o título da página e a hierarquia de headings como metadado.
- Tamanho alvo: 400-600 tokens. Seções maiores são subdivididas por parágrafo.
- Links internos: quando uma seção referencia outra página, adicionar ao metadado do chunk um resumo de 1-2 frases da página referenciada. Isso permite que o modelo entenda a referência sem precisar de um chunk adicional.
- Macros: macros com conteúdo estático (expand, info, note, warning) são expandidas no texto. Macros dinâmicas (jira-issues, roadmap) são substituídas por placeholder descritivo (ex: "[Lista de issues do Jira relacionadas — conteúdo dinâmico não disponível]").

### 5.5 Planilhas Excel

**Estratégia: conversão para formato descritivo + chunking por bloco lógico.**

Planilhas são convertidas em duas camadas:

**Camada 1 — Dados como tabelas:** Cada aba é convertida para markdown table (usando openpyxl para ler valores resolvidos, não fórmulas). Cada tabela se torna um chunk. Se a aba tiver mais de ~30 linhas, segmentar por blocos lógicos com cabeçalhos repetidos.

**Camada 2 — Regras como texto:** Para planilhas com lógica de cálculo, criar descrições textuais das regras de negócio. Exemplo: em vez de `=SE(B2="Fracionada"; C2*0,15; C2*0,08)`, gerar o chunk: "Para cargas fracionadas, o frete é calculado como 15% do valor da carga. Para cargas completas, o frete é 8% do valor da carga. Fonte: planilha Cálculo_Frete.xlsx, aba Regras." Essa camada exige curadoria humana ou, no mínimo, validação humana de descrições geradas por LLM.

**Overlap:** Não aplicável a chunks tabulares (são auto-contidos). Aplicável apenas a descrições textuais longas (overlap de 50 tokens).

**Atualização mensal:** O pipeline deve detectar planilhas alteradas (via timestamp ou hash), re-converter e re-indexar apenas os chunks afetados. Versionamento dos chunks com data permite que o modelo identifique a versão mais recente quando há conflito.

---

## 6. Estratégia de Retrieval

### 6.1 Componentes Recomendados

**Busca Vetorial (baseline):** Embedding de cada chunk com text-embedding-ada-002 (ou text-embedding-3-large para maior precisão, a custo marginal adicional), indexado em Azure AI Search. A busca vetorial captura similaridade semântica — quando o atendente pergunta "prazo de entrega para o interior de Minas", encontra chunks sobre "SLA para destinos em MG fora da capital" mesmo sem correspondência lexical exata.

Limitação da busca vetorial pura: queries sobre valores específicos ("qual o valor do frete para carga de 500kg SP-RJ?") podem retornar chunks semanticamente próximos mas com valores errados (ex: chunk sobre SP-BH em vez de SP-RJ), porque a distância semântica entre rotas diferentes é pequena.

**Busca Híbrida (recomendada):** Combinação de busca vetorial + busca lexical (BM25). Azure AI Search suporta nativamente busca híbrida com Reciprocal Rank Fusion (RRF) para combinar os rankings. A busca lexical complementa a vetorial em queries com termos específicos (códigos de rota, nomes de cidades, siglas de tipo de carga) que precisam de correspondência exata.

**Re-ranking (obrigatório):** Após a busca híbrida retornar os top-50 candidatos, aplicar um cross-encoder re-ranker para selecionar os top-12-20 finais. O re-ranker (Cohere Rerank, ou um cross-encoder como ms-marco-MiniLM) avalia cada par (query, chunk) de forma mais precisa que a busca vetorial, que compara embeddings pré-computados independentemente.

O re-ranking é o componente de maior impacto na qualidade do RAG da NovaTech, porque é a última linha de defesa antes do contexto ser montado. Um chunk irrelevante que sobrevive ao re-ranking desperdiça um dos 12-20 slots disponíveis.

**Parent-Child Retrieval:** Conforme descrito na estratégia de chunking: child chunks (granulares) são indexados e recuperados; ao serem selecionados, seus parent chunks (contexto amplo) são incluídos no contexto. Isso é especialmente importante para tabelas de frete onde o child chunk contém as linhas relevantes e o parent contém as notas e condições que qualificam os valores.

**Metadata Filtering (pré-retrieval):** Antes da busca vetorial, aplicar filtros baseados em metadados para reduzir o espaço de busca:

- **Área:** Se a query é sobre compliance, filtrar para documentos da área de Compliance.
- **Tipo de documento:** Se a query é sobre valores/tarifas, priorizar planilhas e tabelas.
- **Data:** Priorizar versões mais recentes quando há múltiplas versões.
- **Confiança de OCR:** Excluir ou deprioritizar chunks com confiança baixa.

A detecção de área/tipo pode ser feita por um classificador leve (um prompt ao LLM ou um classifier fine-tuned) aplicado à query do usuário antes do retrieval.

### 6.2 Combinação Recomendada (Pipeline Completo)

```
Query do atendente
  → [1] Classificação da query (área, tipo de conteúdo esperado)
  → [2] Metadata filtering (reduz escopo)
  → [3] Busca híbrida (vetorial + BM25) → top-50 candidatos
  → [4] Re-ranking (cross-encoder) → top-15 chunks
  → [5] Parent expansion (adiciona parent chunks onde aplicável)
  → [6] Deduplicação e ordenação por relevância
  → [7] Montagem do contexto (sanduíche: relevantes nas extremidades)
  → [8] Chamada ao GPT-4o com contexto montado
  → [9] Resposta com citação de fontes
```

### 6.3 Tratamento de Contradições entre Documentos

A NovaTech informou que documentos se contradizem entre versões. Isso é um risco significativo para RAG, porque o modelo pode receber chunks contraditórios no mesmo contexto e gerar uma resposta que mistura informações de versões diferentes.

Estratégia de mitigação em três camadas:

**Camada 1 — Governança (pré-indexação):** Na ingestão, atribuir a cada documento um status de versão (vigente, substituído, rascunho). Apenas documentos "vigentes" são incluídos no índice principal. Documentos substituídos vão para um índice separado, acessível apenas sob demanda explícita.

**Camada 2 — Metadados (retrieval):** Cada chunk carrega data de atualização e versão. O re-ranker prioriza versões mais recentes. Se dois chunks contraditórios forem selecionados, o sistema pode detectar isso (mesmo documento, datas diferentes) e incluir apenas o mais recente.

**Camada 3 — Instrução no prompt (geração):** O system prompt instrui o modelo: "Se você encontrar informações contraditórias entre fontes, priorize a fonte com data mais recente e informe ao atendente que há versões conflitantes, indicando ambas as fontes para verificação."

Esta terceira camada é uma rede de segurança, não uma solução. A resolução real de contradições exige governança documental, que está fora do escopo técnico mas deve ser fortemente recomendada à NovaTech.

---

## 7. Arquitetura Recomendada

### 7.1 Visão Geral

A arquitetura se divide em dois pipelines: ingestão (offline, batch) e consulta (online, real-time).

**Pipeline de Ingestão (batch, mensal + on-demand):**

```
Fontes (SharePoint, Confluence, Pasta de Rede)
  → Conectores (Microsoft Graph API, Confluence REST API, File System)
  → Extração (Azure Document Intelligence para PDFs, API para Confluence, openpyxl para Excel)
  → Pré-processamento (limpeza, normalização, OCR, extração de tabelas)
  → Chunking (estratégia por tipo de fonte, conforme Capítulo 5)
  → Embedding (text-embedding-ada-002 via Azure OpenAI)
  → Indexação (Azure AI Search com índice vetorial + BM25)
  → Metadados (Cosmos DB ou storage account para versioning e governança)
```

**Pipeline de Consulta (real-time, <5s latência):**

```
Atendente (Teams)
  → Bot Framework / Power Virtual Agents
  → Classificação de query
  → Metadata filtering + Busca híbrida (Azure AI Search)
  → Re-ranking
  → Montagem de contexto
  → GPT-4o (Azure OpenAI)
  → Resposta formatada com fontes
  → Teams (resposta ao atendente)
```

### 7.2 Stack Tecnológica

| Componente               | Tecnologia                                         | Justificativa                                                                             |
| ------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Orquestração de LLM      | Azure OpenAI (GPT-4o)                              | Licenças Microsoft existentes; compliance; SLA enterprise                                 |
| Embeddings               | text-embedding-ada-002 ou text-embedding-3-large   | Custo baixo; integração nativa Azure                                                      |
| Índice vetorial + busca  | Azure AI Search                                    | Busca híbrida nativa; integração Azure; managed service                                   |
| Extração de PDFs         | Azure Document Intelligence                        | Extração tabular; OCR integrado; superior a alternativas OSS para documentos corporativos |
| Extração Confluence      | API REST + HTML parser (BeautifulSoup)             | Acesso programático padrão                                                                |
| Extração Excel           | openpyxl (Python)                                  | Leitura de valores resolvidos e fórmulas                                                  |
| Orquestração de pipeline | Azure Functions ou LangChain/LlamaIndex            | Serverless para pipeline de consulta; framework RAG para lógica de retrieval              |
| Interface                | Microsoft Teams (Bot Framework)                    | Integração nativa com ambiente Microsoft da NovaTech                                      |
| Re-ranking               | Cohere Rerank ou modelo cross-encoder via Azure ML | Componente de maior impacto na qualidade                                                  |
| Monitoramento            | Azure Application Insights + logging customizado   | Rastreabilidade de queries, chunks recuperados, respostas                                 |

### 7.3 Considerações de Latência

Alvo: resposta em <5 segundos para manter o fluxo do atendimento.

| Etapa                       | Latência Estimada                     |
| --------------------------- | ------------------------------------- |
| Classificação de query      | 200-500ms (prompt leve ou classifier) |
| Busca híbrida               | 100-300ms                             |
| Re-ranking (top-50)         | 300-800ms                             |
| Parent expansion + montagem | 50-100ms                              |
| GPT-4o (geração)            | 2-4s (streaming)                      |
| **Total**                   | **~3-5s**                             |

O uso de streaming permite que o atendente comece a ler a resposta antes da geração completa, reduzindo a latência percebida.

---

## 8. Riscos Técnicos

### 8.1 Matriz de Riscos

| Risco                                            | Probabilidade | Impacto | Severidade  | Mitigação                                                                                  |
| ------------------------------------------------ | ------------- | ------- | ----------- | ------------------------------------------------------------------------------------------ |
| Tabelas de frete mal extraídas                   | Alta          | Alto    | **Crítico** | Azure Document Intelligence; validação manual de tabelas críticas; QA com perguntas-tipo   |
| Erros silenciosos de OCR                         | Alta          | Alto    | **Crítico** | Score de confiança; validação amostral; flag no prompt                                     |
| Contradições entre versões                       | Alta          | Alto    | **Crítico** | Governança documental; versionamento; instrução no prompt                                  |
| Lost in the Middle degradando respostas          | Média         | Alto    | **Alto**    | Limitar a 12-20 chunks; estratégia sanduíche; re-ranking agressivo                         |
| Macros Confluence com conteúdo invisível         | Média         | Médio   | **Médio**   | Inventário de macros; expansão das estáticas; placeholder para dinâmicas                   |
| Fórmulas Excel não interpretáveis                | Média         | Médio   | **Médio**   | Descrições textuais manuais; snapshot de valores resolvidos                                |
| Prazo de 3 meses insuficiente                    | Alta          | Alto    | **Crítico** | Escopo faseado; go-live parcial (wiki + PDFs textuais); fontes complexas em fase 2         |
| Desatualização do índice                         | Média         | Alto    | **Alto**    | Pipeline de re-ingestão automatizado; alertas de drift                                     |
| Alucinação do modelo sobre dados não encontrados | Média         | Alto    | **Alto**    | Instrução explícita para dizer "não encontrei"; threshold de confiança mínimo no retrieval |
| Latência acima de 5s impactando adoção           | Baixa         | Médio   | **Médio**   | Caching de queries frequentes; streaming; otimização do re-ranker                          |

### 8.2 Riscos de Escalabilidade

O volume atual (14.000 chunks, 192 queries/dia) é confortável. Porém, se a NovaTech expandir para outros departamentos ou adicionar fontes (emails, tickets, ERPs), o volume pode crescer 5-10x. Considerações:

- Azure AI Search escala bem até centenas de milhares de documentos.
- O gargalo de escala será custo de inferência (GPT-4o), não armazenamento ou busca.
- A 10x o volume atual (~1.920 queries/dia), o custo de inferência seria ~$1.150/mês — ainda gerenciável.
- A governança documental, que já é frágil com 1.250 documentos, se tornará inviável em escala maior sem processo formal.

---

## 9. Revisão Crítica

Assumindo agora o papel de um Principal AI Architect revisando este documento, identifico os seguintes problemas:

### 9.1 Estimativas Otimistas

**Premissa de 500 palavras/página para PDFs.** Para documentos com tabelas de 15+ colunas, fluxogramas e formatação corporativa, 500 é possivelmente alto demais. Tabelas com muitas colunas mas valores curtos (datas, siglas, valores monetários) podem gerar muito mais tokens do que palavras naturais quando convertidas para markdown, porque cada separador e espaçamento conta. Revisão: a estimativa de tokens pode estar subestimada em 20-30% para documentos tabulares.

**OCR com taxa de erro de 2-5%.** Essa taxa é para documentos de boa qualidade com Azure Document Intelligence. Para documentos escaneados de impressoras multifuncionais, com resolução variável e possíveis carimbos/anotações manuais, a taxa pode ser 8-15%. E a taxa de erro por chunk (ao menos um erro significativo por chunk) será muito maior que a taxa por caractere.

**Latência de 3-5 segundos.** A estimativa não inclui cold starts de Azure Functions, latência de rede entre componentes, ou variabilidade do GPT-4o em horários de pico. O percentil 95 provavelmente será 6-8 segundos.

**Custo mensal de $115.** Essa estimativa assume ~4.000 tokens por chamada. Com parent expansion, histórico de conversa e system prompts reais, o consumo médio pode ser 6.000-8.000 tokens por chamada, dobrando o custo para ~$230/mês. Ainda gerenciável, mas a projeção original é otimista.

### 9.2 Premissas Frágeis

**"70% dos PDFs são textuais, 30% são escaneados."** Essa proporção foi assumida sem dados. Se a proporção for invertida (70% escaneados), o custo e complexidade do pipeline de ingestão aumentam dramaticamente.

**"Chunks de tabela são auto-contidos."** Uma tabela de frete pode ter notas de rodapé, condições em texto adjacente, e referências a outras tabelas ("para exceções, consulte a tabela 4.2"). Um chunk de tabela sem essas qualificações pode gerar respostas tecnicamente corretas mas operacionalmente erradas.

**"As 3 áreas atualizarão documentos mensalmente de forma coordenada."** A NovaTech explicitamente disse que não tem processo unificado de revisão. A premissa de que o pipeline de re-ingestão resolverá a governança é ingênua. Sem governança documental, o assistente terá dados desatualizados e/ou contraditórios independentemente da qualidade técnica do RAG.

### 9.3 Riscos Ignorados ou Subestimados

**Segurança e controle de acesso.** O documento não aborda se todos os 45 atendentes devem ter acesso a todos os documentos. Se há documentos restritos por área (compliance pode ter documentos que atendimento não deveria ver), o RAG precisa de ACL-aware retrieval — significativamente mais complexo.

**Experiência do usuário e confiança.** O tempo de busca é mensurável (12 min → <2 min), mas a adoção depende de os atendentes confiarem nas respostas. Se o assistente errar em perguntas sobre tabelas de frete (o caso mais frequente e mais suscetível a erros de extração), a confiança será destruída rapidamente, mesmo que funcione bem para perguntas textuais.

**Manutenção contínua.** O documento foca no build, não no run. Quem monitora a qualidade das respostas? Quem re-treina o pipeline quando novos tipos de documento aparecem? Quem lida com edge cases que os atendentes reportam? Sem equipe de manutenção, o assistente degradará progressivamente.

**Multimodalidade.** Fluxogramas como imagens foram tratados superficialmente ("indexar por metadados"). Se esses fluxogramas descrevem processos críticos (procedimento de reclamação, fluxo de devolução), os atendentes não terão resposta para perguntas sobre esses processos, e a utilidade percebida do assistente cairá.

**Queries fora do escopo.** O que acontece quando o atendente pergunta algo que não está na documentação? O modelo precisa de uma estratégia robusta de "não sei" — caso contrário, alucinará. Isso é mais difícil do que parece, porque o modelo recebe chunks (que sempre existirão, mesmo para queries fora do escopo) e tende a construir uma resposta a partir deles.

### 9.4 Ajustes Incorporados à Versão Final

Com base nas críticas acima, os seguintes ajustes foram incorporados nesta versão do documento:

**O que foi alterado:**

- As estimativas de volume incluem agora faixas mais amplas e nota sobre a relação tokens/palavra em português.
- A estimativa de custo foi revisada para considerar o consumo real com parent expansion e histórico.
- A latência inclui nota sobre variabilidade e percentil 95.
- A taxa de erro de OCR foi apresentada como faixa (2-15%) em vez de ponto único.

**O que foi adicionado:**

- Tratamento explícito de contradições entre documentos (3 camadas).
- Risco de segurança e controle de acesso na matriz de riscos.
- Consideração sobre manutenção contínua e equipe de sustentação.
- Estratégia de "não sei" para queries fora do escopo (instrução no prompt + threshold de confiança).
- Recomendação de escopo faseado como mitigação ao prazo de 3 meses.

**Quais riscos receberam maior peso:**

- **Tabelas de frete mal extraídas**: elevado a risco crítico (era alto) — este é o cenário de falha mais provável E mais visível.
- **Contradições entre versões**: elevado a risco crítico — sem governança, é inevitável.
- **Prazo de 3 meses**: elevado a risco crítico — dada a complexidade real das fontes.
- **Governança documental**: adicionado como dependência externa crítica, não apenas mitigação.

---

## 10. Conclusão Final

### Viabilidade: MÉDIA

O projeto é tecnicamente viável, mas com ressalvas significativas que condicionam o sucesso.

**O que funciona bem com RAG neste cenário:**

- Wiki Confluence (fonte mais adequada, 400 páginas, bom para RAG).
- PDFs textuais sem tabelas complexas (manuais de procedimento, políticas).
- Queries textuais ("qual a política de devolução?", "qual o procedimento para reclamação?").

**O que funciona com esforço significativo:**

- Tabelas de frete e SLA (exige extração especializada, chunking cuidadoso, re-ranking).
- PDFs escaneados (exige OCR de qualidade, validação, metadados de confiança).

**O que provavelmente não funciona bem na primeira versão:**

- Queries sobre cálculos complexos de frete (fórmulas interdependentes do Excel).
- Perguntas sobre processos visuais (fluxogramas como imagens).
- Resolução automática de contradições entre versões de documentos.

### Recomendação de Faseamento

**Fase 1 (meses 1-3, go-live):** Wiki Confluence + PDFs textuais do SharePoint (excluindo escaneados). Escopo de ~560 PDFs + 400 páginas wiki. Foco em perguntas sobre procedimentos, políticas e regras textuais. Meta: cobrir ~60% das consultas dos atendentes com qualidade alta.

**Fase 2 (meses 4-5):** Adicionar tabelas de frete e SLA (com extração especializada e validação). Adicionar PDFs escaneados de alta qualidade. Meta: cobrir ~80% das consultas.

**Fase 3 (meses 6-7):** Adicionar planilhas Excel (valores resolvidos + descrições textuais de regras). Adicionar PDFs escaneados de baixa qualidade (com flags de incerteza). Tratamento de fluxogramas via multimodal. Meta: cobrir ~90% das consultas.

**Investimento paralelo obrigatório:** Estabelecer processo de governança documental na NovaTech. Sem isso, o assistente degradará independentemente da qualidade técnica. Designar um "owner" de documentação por área, processo de revisão antes de publicação, e marcação explícita de versão vigente.

### Premissa de Sucesso

O projeto atingirá a meta de <2 minutos por consulta para queries cobertas, mas "cobertas" será um subconjunto da base total. A cobertura crescerá com as fases. A expectativa da diretoria deve ser calibrada: o assistente não substituirá a consulta manual em 100% dos casos no go-live — mas nos casos que cobre, será significativamente mais rápido e consistente.

O fator determinante não será a tecnologia de RAG (que é madura o suficiente), mas a qualidade da ingestão, a governança documental e a estratégia de context engineering que determine quais chunks chegam ao modelo em cada consulta.
