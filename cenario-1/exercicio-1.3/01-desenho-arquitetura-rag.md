Lerei os documentos de apoio antes de estruturar a arquitetura.Ótimo. Tenho todo o contexto necessário. Vou agora construir o desenho técnico completo.

---

## Desenho Técnico da Solução RAG — NovaTech PoC

Antes do diagrama, vale entender o que os documentos revelam sobre os riscos reais desse sistema: a NovaTech não tem apenas um problema de busca — tem um problema de **qualidade de fonte**. Documentos contraditórios (PROC-042 v1 vs v2), fontes informais sem validação (FAQ), gaps de cobertura (frete padrão, carga danificada) e ausência de versionamento formal. A arquitetura precisa tratar esses riscos como cidadãos de primeira classe, não como casos de borda.

---

### 1. Visão geral do pipeline

O pipeline tem seis estágios sequenciais com dois loops de retorno: um de atualização (re-ingestão mensal) e um de qualidade (feedback dos atendentes).---

### 2. Etapas detalhadas

#### Etapa 1 — Ingestão

O objetivo desta etapa é normalizar documentos de três origens heterogêneas em um formato único antes de qualquer processamento semântico.

**Conectores necessários:**

- SharePoint: Microsoft Graph API (autenticação via OAuth2 com credenciais M365 E3 já existentes)
- Confluence: REST API v2 com token pessoal
- Pasta de rede: watch de sistema de arquivos com `watchdog` ou cron diário

**Transformações aplicadas durante a ingestão:**

Cada documento precisa sair dessa etapa com um envelope de metadados completo — sem isso, o retrieval não consegue filtrar por versão, por área responsável ou por nível de confiabilidade da fonte. Os campos obrigatórios são: `doc_id` (hash SHA-256 do conteúdo), `source_type` (sharepoint | confluence | filesystem), `doc_type` (POL | PROC | SLA | FAQ | PLANILHA), `version`, `last_modified`, `responsible_area` (Operações | Compliance | Comercial), `trust_level` (formal | informal), e `superseded_by` (nulo se vigente, referência ao documento substituto se obsoleto).

O campo `trust_level` é especialmente crítico dado o cenário da NovaTech: o FAQ-Atendimento é explicitamente marcado como informal e não validado, e precisa ser tratado como fonte de segunda linha na hora de montar o prompt.

**Deduplicação:** documentos com mesmo SHA-256 são ignorados no re-index. Documentos com mesmo `doc_id` lógico mas versão diferente (como PROC-042 v1 e v2) são **mantidos ambos** — mas a versão mais recente recebe flag `is_current: true`. Isso é deliberado: descartar a v1 quebraria chamados em transição cobertos pela seção 5 da v2.

---

#### Etapa 2 — Chunking

Esta é a decisão técnica mais importante do projeto, porque a natureza dos documentos da NovaTech torna estratégias genéricas inadequadas.

**Por que não usar chunking por tamanho fixo (fixed-size)?**

Documentos como a POL-001 e a SLA-2024 têm tabelas com dados estruturados onde o contexto semântico está na célula + cabeçalho de coluna + cabeçalho de linha juntos. Um chunk por caracteres fixos vai partir uma tabela no meio, criando fragmentos semanticamente incoerentes. O modelo vai receber "Silver | Até 48h úteis" sem saber que isso se refere ao "Tempo de resolução (chamados gerais)".

**Estratégia recomendada: chunking hierárquico por cabeçalho com contexto herdado**

O LangChain tem o `MarkdownHeaderTextSplitter` que segmenta o documento pelos marcadores `#`, `##`, `###`. A lógica é:

Cada chunk herda o contexto hierárquico dos cabeçalhos pai. Um chunk criado a partir da seção `### 3.2. Exceções ao prazo geral` da POL-001 recebe o prefixo de contexto `POL-001 > 3. Regras de Devolução > 3.2. Exceções` embutido no texto do chunk antes da vetorização. Isso resolve o principal problema de retrieval: a pergunta "posso devolver carga perigosa?" vai gerar um embedding próximo ao chunk que fala de exceções de devolução, não ao chunk que fala do prazo geral.

**Tabelas:** tabelas Markdown não são splitadas. Elas são mantidas inteiras como um único chunk, com o cabeçalho imediatamente acima incluído. Isso garante que "Multiplicador regional Norte 1.8" sempre apareça junto com "PROC-042-v2 · Seção 2.1 · Multiplicadores regionais atualizados novembro/2023".

**Parâmetros recomendados:**

- `chunk_size`: 400 tokens (não caracteres — usar `tiktoken` para contar)
- `chunk_overlap`: 80 tokens (20% de sobreposição para não perder contexto de transição entre seções)
- `min_chunk_size`: 60 tokens (chunks menores que isso são descartados ou fundidos com o próximo)

**Tratamento especial para documentos com versão duplicada (PROC-042 v1 e v2):** ambas as versões são ingeridas e chunkeadas normalmente. A diferença está nos metadados: os chunks da v1 recebem `is_current: false` e `superseded_by: "PROC-042-v2"`. No retrieval, isso permite ao filtro de versão priorizar chunks da v2 — mas não excluir a v1, para suportar as disposições transitórias.

---

#### Etapa 3 — Geração de Embeddings

O modelo `all-MiniLM-L6-v2` da sentence-transformers gera vetores de 384 dimensões com boa performance em português, especialmente após fine-tuning multilingual. Para o escopo da PoC, funciona sem ajuste adicional.

**Considerações importantes:**

O modelo tem limite de 256 tokens por sequência. Chunks maiores que isso serão truncados silenciosamente pelo modelo. Por isso o `chunk_size` de 400 tokens deve ser monitorado: tokens do `tiktoken` (GPT-4) não são os mesmos tokens do BERT usado pelo MiniLM. Na prática, 400 tokens GPT ≈ 300-350 tokens BERT, que ficam abaixo do limite de 256 do MiniLM com a maioria dos textos. Para garantir, o pipeline deve medir o tamanho com o tokenizador do próprio modelo antes de enviar.

**Estratégia de indexação:** os chunks são vetorizados em batch (128 por vez para caber em RAM em CPU), e os vetores são persistidos no ChromaDB junto com os metadados completos de cada chunk. O tempo estimado de indexação para ~1.200 documentos da NovaTech real é de 15-40 minutos em CPU — aceitável para um processo batch noturno ou semanal.

---

#### Etapa 4 — Armazenamento Vetorial (ChromaDB)

**Estrutura de coleções:**

Ao invés de uma única coleção flat, o projeto usa **duas coleções separadas**:

`novatech_formal` — documentos com `trust_level: formal` (POL, PROC, SLA). Esta coleção é a fonte primária para respostas.

`novatech_informal` — documentos com `trust_level: informal` (FAQ, wikis não oficiais). Esta coleção só é consultada quando a busca na coleção formal não retorna chunks com score acima do threshold mínimo.

Essa separação é a resposta técnica ao risco identificado no cenário: o FAQ-Atendimento contém informações úteis mas não validadas. Retorná-lo com a mesma confiança que um documento POL seria um problema sério para um sistema de atendimento ao cliente.

**Schema de metadados no ChromaDB:**

```
{
  "doc_id":        "sha256:...",
  "source_file":   "POL-001-politica-devolucao.md",
  "doc_type":      "POL",
  "section_path":  "3. Regras de Devolução > 3.2. Exceções",
  "version":       "3.1",
  "is_current":    true,
  "trust_level":   "formal",
  "last_modified": "2024-01-15",
  "responsible":   "Diretoria de Operações"
}
```

---

#### Etapa 5 — Retrieval com Reranking

Esta etapa responde à pergunta: dos ~3.000-5.000 chunks indexados, quais os 3-5 mais relevantes para a pergunta do atendente?

**Fluxo em três camadas:**

**Camada 1 — busca semântica primária:** query embedding gerado com o mesmo modelo (all-MiniLM-L6-v2), busca por similaridade cosseno no ChromaDB, recupera top-15 da coleção `novatech_formal`.

**Camada 2 — filtro de versão:** entre os top-15, se houver chunks de v1 e v2 do mesmo documento, os de v1 têm seu score reduzido por um fator de penalização (0.7× por padrão). Isso não elimina a v1 — mantém ela disponível para casos de transição — mas garante que a v2 seja preferida quando ambas são relevantes.

**Camada 3 — fallback para informal:** se nenhum chunk da coleção formal superar score de 0.65 (threshold calibrado nos testes), o sistema repete a busca na coleção `novatech_informal` e sinaliza no prompt que os chunks recuperados são de fonte não oficial.

**Resultado:** os 3-5 chunks com maior score são passados para a montagem do prompt, cada um acompanhado de seus metadados completos.

---

#### Etapa 6 — Montagem do Prompt e Geração

Esta é a etapa que transforma chunks em resposta útil — e onde a maioria dos problemas de alucinação e inconsistência acontecem.

**Template estruturado do prompt:**

```
[SYSTEM]
Você é um assistente de atendimento da NovaTech.
Responda APENAS com base nos trechos de documentação fornecidos.
Se a informação não estiver nos trechos, diga que não encontrou
cobertura e sugira escalar para a área responsável.
Nunca invente informações. Nunca misture versões de documentos.

[CONTEXTO]
{chunks_formatados}
— onde cada chunk tem: [FONTE: {doc_type}-{version} | {section_path} |
  Confiabilidade: {trust_level}]

[INSTRUÇÃO]
Pergunta do atendente: {pergunta}

Responda de forma objetiva, cite a fonte de cada informação,
e indique se há versões conflitantes de documentos.

[RESPOSTA]
```

**Mecanismo de detecção de conflito:** antes de montar o prompt, o pipeline verifica se os chunks recuperados incluem versões diferentes do mesmo documento (ex: PROC-042 v1 e v2). Se sim, insere uma instrução adicional: "Atenção: foram recuperadas versões conflitantes de {doc_id}. Apresente as duas versões e indique qual é a mais recente."

**Integração com Claude:** na PoC, a geração é feita manualmente — o atendente copia o prompt montado e cola no chat do Claude. Isso é deliberado: permite validar a qualidade das respostas antes de automatizar a integração via API.

---

### 3. Estratégia de chunking — justificativa técnica aprofundada

O chunking hierárquico por cabeçalho é a escolha correta para o corpus da NovaTech por quatro razões específicas:

**Razão 1 — preservação de contexto normativo.** Documentos POL e PROC têm seções que só fazem sentido no contexto da seção pai. A seção 3.2 de POL-001 ("Exceções ao prazo geral") precisa carregar consigo que está dentro de "3. Regras de Devolução" — caso contrário, um chunk sobre "cargas perigosas não são elegíveis" pode ser recuperado para perguntas sobre frete de cargas perigosas quando a pergunta era sobre devolução.

**Razão 2 — integridade de tabelas.** Tabelas em Markdown são estruturas bidimensionais onde o significado está na interseção de linha e coluna. Splittar por tamanho fixo invariavelmente produz fragmentos como "| 1.8 |" sem contexto — inúteis para o modelo. Manter tabelas inteiras como chunks únicos sacrifica granularidade mas garante semântica.

**Razão 3 — rastreabilidade de fonte.** Cada chunk precisa apontar para uma seção específica do documento original. Com chunking por cabeçalho, a `section_path` é gerada automaticamente pelo splitter — com chunking por tamanho fixo, exigiria heurísticas adicionais para inferir a qual seção um chunk pertence.

**Razão 4 — compatibilidade com o modelo de embedding.** O `all-MiniLM-L6-v2` foi treinado com sentenças e parágrafos, não com fragmentos arbitrários de texto. Chunks que respeitam fronteiras semânticas naturais (seções, parágrafos, tabelas) geram embeddings de melhor qualidade que fragmentos gerados por janela deslizante.

---

### 4. Estrutura de diretórios do projeto

```
novatech-rag-poc/
│
├── README.md
├── requirements.txt
├── .env.example                    # CHROMA_PATH, MODEL_NAME, etc.
│
├── data/
│   ├── raw/                        # documentos originais (não commitados)
│   │   ├── POL-001-politica-devolucao.md
│   │   ├── PROC-042-frete-especial-v1.md
│   │   ├── PROC-042-v2-frete-especial-revisado.md
│   │   ├── SLA-2024-tabela-sla-clientes.md
│   │   └── FAQ-atendimento.md
│   ├── processed/                  # chunks após processamento (JSON)
│   └── chroma_db/                  # persistência do ChromaDB (não commitado)
│
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py               # carrega .md, .pdf, .docx de disco
│   │   ├── metadata_extractor.py   # extrai versão, data, área do cabeçalho YAML
│   │   └── document_registry.py   # controla doc_id, is_current, superseded_by
│   │
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── markdown_splitter.py    # wrapper do MarkdownHeaderTextSplitter
│   │   ├── table_handler.py        # detecta e preserva tabelas Markdown inteiras
│   │   └── context_injector.py     # injeta section_path no texto do chunk
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedder.py             # sentence-transformers, batch, token check
│   │
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   ├── chroma_client.py        # inicializa coleções formal/informal
│   │   └── indexer.py              # upsert com deduplicação por SHA-256
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── retriever.py            # busca semântica top-k
│   │   ├── version_filter.py       # penalização de versões obsoletas
│   │   └── conflict_detector.py   # detecta chunks contraditórios nos resultados
│   │
│   ├── prompt/
│   │   ├── __init__.py
│   │   ├── template.py             # templates de prompt por tipo de consulta
│   │   └── assembler.py            # monta prompt final com chunks + metadados
│   │
│   └── utils/
│       ├── token_counter.py        # conta tokens com tokenizador do modelo
│       └── logger.py               # logging estruturado (JSON)
│
├── scripts/
│   ├── build_index.py              # script de ingestão completa (roda em batch)
│   ├── query_interactive.py        # CLI para testar queries manualmente
│   └── eval_retrieval.py           # avalia precisão do retrieval contra gabarito
│
├── tests/
│   ├── test_chunking.py
│   ├── test_retrieval.py           # testa os 10 cenários do Anexo B
│   └── fixtures/                   # documentos de teste
│
└── notebooks/
    ├── 01_exploratory_chunking.ipynb   # análise dos chunks gerados
    ├── 02_retrieval_quality.ipynb      # avaliação de recall/precision
    └── 03_prompt_experiments.ipynb     # testes de templates de prompt
```

---

### 5. Diagrama detalhado: retrieval e montagem do prompt---

### 6. Riscos operacionais e limitações técnicas

Os riscos abaixo foram derivados diretamente da análise dos documentos da NovaTech — não são riscos genéricos de RAG.

**Risco 1 — Contaminação por versão obsoleta (Alta criticidade)**
A PROC-042 v1 e v2 coexistem sem hierarquia formal. O pipeline mitiga com filtro de versão, mas se o threshold de penalização estiver mal calibrado, o sistema pode retornar multiplicadores incorretos (ex: Norte 1.6 ao invés de 1.8). Impacto: erro financeiro no cálculo de frete. Mitigação: teste de regressão específico para os 10 cenários do Anexo B antes de qualquer deploy.

**Risco 2 — Alucinação por gap de cobertura (Alta criticidade)**
Perguntas sobre frete padrão (abaixo de 500kg), política de carga danificada e seguro de carga não têm cobertura em documentos formais. O modelo de linguagem pode inferir respostas plausíveis mas incorretas. Mitigação: o template de prompt precisa ser explícito que ausência de chunk relevante = "não encontrei cobertura, escale para [área]", nunca uma resposta inventada.

**Risco 3 — Elevação de confiança do FAQ informal (Média criticidade)**
O FAQ-Atendimento contém informações úteis mas tecnicamente não validadas. Se retornado com a mesma sinalização visual que documentos POL/PROC, o atendente pode citá-lo como fonte oficial. Mitigação: coleção separada + label explícito "FONTE INFORMAL — confirmar na documentação normativa" no prompt.

**Risco 4 — Fragmentação de tabelas em re-ingestão (Média criticidade)**
A tabela de multiplicadores regionais muda mensalmente. Se o processo de re-ingestão não fizer upsert correto (deletar chunks antigos + inserir novos), chunks da tabela antiga e da nova podem coexistir no ChromaDB com embeddings muito próximos. Mitigação: implementar deleção explícita por `doc_id` antes de re-indexar.

**Risco 5 — Limite de tokens do modelo de embedding (Baixa criticidade na PoC, Alta em produção)**
O `all-MiniLM-L6-v2` trunca em 256 tokens. Chunks maiores (especialmente tabelas grandes da SLA) perdem informação ao ser vetorizados. Na PoC com os 5 documentos do Anexo A, isso não é problema. Em produção com 800 documentos do SharePoint, pode afetar recall. Mitigação: medir distribuição de tamanho dos chunks antes de escalar; considerar migrar para `all-mpnet-base-v2` (512 tokens) se necessário.

**Risco 6 — Ausência de baseline de avaliação (Organizacional)**
A NovaTech não tem histórico estruturado de perguntas de atendimento com respostas corretas validadas. Sem um conjunto de avaliação (golden dataset), é impossível medir se o sistema melhorou ou piorou com mudanças. Mitigação: durante a PoC, coletar 50-100 pares pergunta/resposta-correta com os atendentes sênior para construir o primeiro golden dataset.

**Limitação técnica — ChromaDB não é adequado para produção em escala**
ChromaDB é excelente para PoC e desenvolvimento local, mas não suporta busca aproximada eficiente (HNSW configurável), multi-tenancy ou alta disponibilidade. Para a versão de produção com Azure AI Search, a migração é direta: a interface do LangChain abstrai o vector store, então trocar `Chroma` por `AzureSearch` é uma mudança de 10 linhas de código.

---

### Resumo executivo da arquitetura

A solução proposta tem três características que a diferenciam de uma implementação ingênua de RAG. Primeiro, trata a qualidade da fonte como variável explícita — documentos informais ficam em coleção separada e são sinalizados como tal no prompt. Segundo, resolve o problema de versões conflitantes com filtro de penalização no retrieval em vez de escolher arbitrariamente uma versão para indexar. Terceiro, é desenhada para evoluir: a separação em módulos independentes (ingestion, chunking, retrieval, prompt) permite substituir componentes individuais sem reescrever o pipeline — o que é essencial dado o cronograma de 3 meses.

A PoC com os 5 documentos do Anexo A é suficiente para validar os aspectos técnicos mais arriscados: qualidade do retrieval para perguntas multi-domínio, comportamento do sistema diante de conflitos de versão, e eficácia do template de prompt em evitar alucinações por gap de cobertura.
