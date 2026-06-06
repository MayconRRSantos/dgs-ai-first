## Problemas Encontrados e Propostas de Correção

**NovaTech RAG PoC — Relatório Técnico | Tech Lead Review**
Baseado nos resultados dos 5 testes de retrieval e na avaliação do pipeline completo.

---

Antes de detalhar cada problema, vale registrar o padrão geral observado: os testes confirmaram que o **template de prompt e os guardrails de geração estão funcionando** — o LLM não aluci­nou em nenhum dos cinco casos. O gargalo está inteiramente no **retrieval**. Dois testes falharam por completo em recuperar o chunk primário esperado (Testes 1 e 3), dois recuperaram os documentos certos mas as seções erradas (Testes 2 e 4), e um recuperou o chunk certo mas na posição menos influente do contexto (Teste 5). Isso significa que qualquer investimento agora em refinar o prompt é prematuro — o problema está upstream.

Foram identificados **quatro problemas**, ordenados por criticidade operacional.

---

### Problema 1 — Dominância de fontes informais no ranking de recuperação

**Descrição**

Em 4 dos 5 testes realizados, chunks do FAQ-atendimento apareceram no top-3 do retrieval, com scores entre 0.77 e 0.81 — frequentemente acima de documentos formais (POL, PROC, SLA) que continham a resposta correta. No Teste 5, o chunk autoritativo (POL-001-B, que define claramente a proibição de devolução de carga perigosa) ficou em 4º lugar com score 0.7471, abaixo de três chunks informais com scores superiores. No Teste 1, três dos quatro chunks recuperados eram do FAQ, sendo que dois eram completamente irrelevantes para a pergunta.

**Causa provável**

O FAQ foi redigido em linguagem coloquial que replica diretamente a forma como atendentes fazem perguntas. O título de cada item — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" — é semanticamente muito próximo de consultas em linguagem natural como "Posso devolver carga perigosa?". Documentos formais (POL, PROC) usam linguagem normativa e técnica, gerando embeddings em regiões do espaço vetorial mais distantes das perguntas conversacionais. Com uma única coleção flat no ChromaDB, o modelo de embedding não tem como distinguir autoridade de fonte — apenas similaridade semântica superficial.

**Impacto**

Alto. Em produção, um atendente que receba uma resposta construída predominantemente a partir do FAQ pode transmitir ao cliente informações não validadas com aparência de oficialidade. O caso mais crítico seria o Teste 5: se o LLM ponderasse os três primeiros chunks (todos informais) acima do quarto (formal), poderia suavizar a proibição de devolução de carga perigosa — gerando risco regulatório e de compliance. O guardrail de prompt mitigou isso neste teste, mas a dependência de guardrail para compensar falha de retrieval não é arquitetura robusta.

**Correção proposta**

A solução é implementar a separação em duas coleções ChromaDB, conforme previsto na arquitetura original mas não executado na PoC:

```python
# vectorstore/chroma_client.py

import chromadb

def get_collections(persist_path: str):
    client = chromadb.PersistentClient(path=persist_path)

    formal = client.get_or_create_collection(
        name="novatech_formal",
        metadata={"hnsw:space": "cosine"}
    )
    informal = client.get_or_create_collection(
        name="novatech_informal",
        metadata={"hnsw:space": "cosine"}
    )
    return formal, informal
```

```python
# retrieval/retriever.py

FORMAL_THRESHOLD = 0.65  # score mínimo para aceitar resultado formal

def retrieve(query: str, embedder, formal_col, informal_col, top_k: int = 5):
    query_vec = embedder.encode([query])[0].tolist()

    # Busca primária: apenas coleção formal
    formal_results = formal_col.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    scores = [1 - d for d in formal_results["distances"][0]]
    best_formal_score = max(scores) if scores else 0

    if best_formal_score >= FORMAL_THRESHOLD:
        return _format_results(formal_results, source_type="formal")

    # Fallback: coleção informal, com sinalização obrigatória
    informal_results = informal_col.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    return _format_results(informal_results, source_type="informal")
```

Com essa estrutura, chunks do FAQ nunca competem diretamente com documentos POL/PROC/SLA no ranking. O FAQ só entra no contexto do prompt quando a busca formal não encontra cobertura suficiente — e nesse caso chega sinalizado como informal, mantendo o guardrail de prompt como segunda linha de defesa.

---

### Problema 2 — Versão obsoleta do documento PROC-042 rankeia acima da versão vigente

**Descrição**

No Teste 2, o chunk de multiplicadores regionais da PROC-042 v1 (versão de março/2023) ficou em 1º lugar com score 0.8212, enquanto o chunk equivalente da PROC-042-v2 (versão de novembro/2023, vigente para chamados após 01/12/2023) ficou em 2º com score 0.8025. A diferença de score é pequena (0.019), mas suficiente para inverter a ordenação. Se o LLM der peso proporcional à posição no contexto — comportamento comum — a resposta usaria Norte = 1.6 (v1) em vez de Norte = 1.8 (v2), gerando erro financeiro direto no cálculo de frete.

**Causa provável**

Dois fatores combinados. Primeiro, a PROC-042 v1 tem texto mais curto e denso (a seção 2.1 contém apenas a tabela de multiplicadores, sem texto adicional), o que tende a gerar embeddings mais "concentrados" e com maior similaridade para consultas diretas sobre multiplicadores. Segundo, o ChromaDB na configuração atual não tem conhecimento do atributo `is_current` dos metadados ao calcular o score de similaridade — o ranking é puramente vetorial, sem qualquer sinal de autoridade ou vigência. Ambos os documentos coexistem na mesma coleção sem hierarquia explícita.

**Impacto**

Alto — direto e mensurável. O multiplicador Norte na v1 é 1.6 e na v2 é 1.8, uma diferença de 12.5%. Para um frete com valor base de R$ 10.000 e fator de peso 1.15 (carga entre 1.001kg e 3.000kg), isso representa uma diferença de R$ 1.380 no valor final cobrado ao cliente. Em escala, com 320 chamados/dia e ~60% envolvendo consulta a documentação, o impacto financeiro acumulado de respostas baseadas na versão errada seria significativo.

**Correção proposta**

Implementar um filtro de penalização pós-retrieval que reduz o score efetivo de chunks marcados como `is_current: false`. Isso não elimina a versão antiga do índice — ela precisa existir para suportar as disposições transitórias — mas garante que a versão vigente seja preferida quando ambas são relevantes:

```python
# retrieval/version_filter.py

VERSION_PENALTY = 0.75  # multiplicador aplicado a versões não-vigentes

def apply_version_filter(results: list[dict]) -> list[dict]:
    """
    Penaliza chunks de versões obsoletas e reordena por score efetivo.
    Mantém chunks obsoletos disponíveis (para disposições transitórias),
    mas garante que versões vigentes fiquem acima no ranking.
    """
    for chunk in results:
        if not chunk["metadata"].get("is_current", True):
            original_score = chunk["score"]
            chunk["score"] = original_score * VERSION_PENALTY
            chunk["metadata"]["version_warning"] = (
                f"⚠️ Versão obsoleta. Score ajustado: "
                f"{original_score:.4f} → {chunk['score']:.4f}. "
                f"Versão vigente: {chunk['metadata'].get('superseded_by', 'verificar')}"
            )

    return sorted(results, key=lambda x: x["score"], reverse=True)
```

```python
# retrieval/conflict_detector.py

def detect_version_conflict(results: list[dict]) -> dict:
    """
    Verifica se o resultado contém versões diferentes do mesmo documento lógico.
    Retorna metadados de conflito para uso no Prompt Builder.
    """
    doc_versions = {}
    for chunk in results:
        doc_id = chunk["metadata"].get("doc_logical_id")  # ex: "PROC-042"
        version = chunk["metadata"].get("version")
        if doc_id:
            doc_versions.setdefault(doc_id, set()).add(version)

    conflicts = {
        doc_id: versions
        for doc_id, versions in doc_versions.items()
        if len(versions) > 1
    }
    return conflicts  # ex: {"PROC-042": {"v1", "v2"}}
```

O resultado do `conflict_detector` é passado ao Prompt Builder, que injeta uma instrução adicional no prompt quando conflito é detectado — mantendo o guardrail de geração como segunda linha de defesa mesmo após a correção no retrieval.

---

### Problema 3 — Embeddings de tabelas Markdown têm baixa recuperabilidade semântica

**Descrição**

Dois testes falharam inteiramente por não recuperar chunks baseados em tabelas: no Teste 3 (SLA Gold), a seção 2 do SLA-2024 — que contém a tabela com os tempos de resposta e resolução por tier — não apareceu entre os top-4, sendo substituída pelas seções 5, 1 e 4 do mesmo documento. No Teste 4 (frete acima de 500kg), as tabelas de fórmula e multiplicadores (seções 2 e 2.1 da PROC-042-v2) não foram recuperadas — apenas as seções de Objetivo (texto corrido). Em ambos os casos, as seções com maior valor operacional para o atendente ficaram fora do contexto enviado ao LLM.

**Causa provável**

O modelo `all-MiniLM-L6-v2` foi treinado predominantemente com pares de sentenças em prosa. Uma tabela Markdown como a abaixo tem estrutura sintática que o tokenizador processa de forma subótima:

```
| Gold | Até 2h úteis | Até 24h úteis |
| Silver | Até 4h úteis | Até 48h úteis |
```

O embedding resultante captura a presença de termos como "Gold", "úteis" e os valores numéricos, mas não codifica eficientemente a relação semântica entre eles (Gold → 2h → resposta). Uma pergunta como "Qual o SLA para cliente Gold?" gera um embedding que busca por texto que relacione "Gold" e "SLA" em prosa — e a seção de medição (Seção 5) ou classificação (Seção 1) satisfazem melhor essa busca por conterem mais texto corrido com esses termos.

**Impacto**

Alto. As tabelas são exatamente o conteúdo mais consultado em operações de atendimento: multiplicadores de frete, tempos de SLA, faixas de desconto por volume, penalidades. Se os chunks de tabela sistematicamente não são recuperados, o sistema falha nas consultas mais frequentes e de maior impacto operacional — precisamente o oposto do objetivo do projeto.

**Correção proposta**

Implementar prefixação semântica de tabelas durante o chunking. Antes de gerar o embedding, cada chunk de tabela recebe um prefixo em linguagem natural que descreve o conteúdo estruturado da tabela. O embedding é gerado sobre o texto prefixado, mas apenas o conteúdo original da tabela é armazenado e exibido no prompt:

```python
# chunking/table_handler.py

import re

TABLE_PATTERN = re.compile(r"(\|.+\|[\r\n]+)+", re.MULTILINE)

def is_table_chunk(text: str) -> bool:
    return bool(TABLE_PATTERN.search(text))

def generate_table_prefix(chunk_text: str, metadata: dict) -> str:
    """
    Gera prefixo em linguagem natural para chunks de tabela.
    O prefixo é usado APENAS para gerar o embedding — não é armazenado.
    """
    section = metadata.get("section_path", "")
    doc_type = metadata.get("doc_type", "")

    prefix_map = {
        "SLA": (
            "Tabela de níveis de serviço por tipo de cliente. "
            "Contém tempos de resposta e resolução para Gold, Silver e Standard. "
        ),
        "PROC": (
            "Tabela de parâmetros de cálculo de frete especial. "
            "Contém multiplicadores regionais e fatores de peso por faixa. "
        ),
        "POL": (
            "Tabela de regras e exceções de política. "
        ),
    }

    base_prefix = prefix_map.get(doc_type, "Tabela de referência. ")
    return f"{base_prefix}Seção: {section}. Conteúdo:\n{chunk_text}"


def embed_with_prefix(chunk_text: str, metadata: dict, embedder) -> list[float]:
    """
    Gera embedding com prefixo semântico para tabelas.
    Para texto corrido, usa o texto original sem modificação.
    """
    if is_table_chunk(chunk_text):
        text_for_embedding = generate_table_prefix(chunk_text, metadata)
    else:
        text_for_embedding = chunk_text

    return embedder.encode([text_for_embedding])[0].tolist()
```

Complementarmente, aumentar `top_k` de 4 para 8 no retrieval e aplicar reranking com um modelo cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) antes de selecionar os 4 chunks finais para o prompt. O cross-encoder avalia a relevância de cada chunk em relação à query de forma conjunta, não como vetores independentes, e tende a recuperar melhor tabelas que o bi-encoder:

```python
# retrieval/reranker.py

from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, chunks: list[dict], top_n: int = 4) -> list[dict]:
    pairs = [(query, chunk["document"]) for chunk in chunks]
    scores = reranker.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    return sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)[:top_n]
```

---

### Problema 4 — Seções introdutórias superam seções operacionais no ranking por sobreposição lexical

**Descrição**

No Teste 4 ("Como funciona o frete para cargas acima de 500kg?"), os chunks de seção de Objetivo de ambas as versões da PROC-042 ficaram em 1º e 2º lugar — apesar de conterem apenas uma frase introdutória com baixo valor operacional. Os chunks com a fórmula real e os multiplicadores (seções 2 e 2.1) não foram recuperados. No Teste 1, a seção de Custos (3.5) foi recuperada acima da seção de Prazo (3.1), apesar de a pergunta ser explicitamente sobre prazo.

**Causa provável**

As seções de Objetivo mencionam explicitamente o termo "500kg" — o mesmo que aparece na pergunta. O modelo de embedding do tipo bi-encoder (como o MiniLM) tende a capturar sobreposição lexical mesmo dentro de representações semânticas, especialmente para termos específicos como valores numéricos. A seção de Objetivo tem texto curto e denso, com alta concentração do termo-chave, gerando alta similaridade com a query. As seções operacionais (com fórmulas e tabelas) contêm termos técnicos mais específicos ("multiplicador regional", "fator de peso") que divergem do vocabulário da pergunta em linguagem natural.

**Impacto**

Médio-alto. O sistema recupera o documento correto mas a seção errada — um resultado que parece bom no nível do documento mas falha no nível do chunk, que é a unidade que efetivamente entra no prompt. O LLM recebe contexto que confirma que existe um procedimento para cargas acima de 500kg, mas não recebe os parâmetros necessários para responder a pergunta operacionalmente. O atendente obtém uma resposta que o instrui a escalar para o Comercial, quando a documentação técnica estava disponível na base.

**Correção proposta**

Duas ações complementares. A primeira é implementar query expansion no momento do retrieval — a pergunta original é expandida com variações técnicas antes de gerar o embedding de busca. Isso amplia a cobertura semântica da query para capturar chunks com vocabulário mais especializado:

```python
# retrieval/query_expander.py

EXPANSION_MAP = {
    "frete":         ["cálculo de frete", "valor do frete", "multiplicador regional",
                      "fator de peso", "frete especial"],
    "devolução":     ["prazo de devolução", "dias úteis", "coleta reversa",
                      "elegível para devolução"],
    "sla":           ["tempo de resposta", "tempo de resolução", "horas úteis",
                      "incidente crítico"],
    "carga perigosa":["classes ANTT", "Resolução ANTT", "gestão de riscos",
                      "classe 1", "classe 6"],
    "prazo":         ["dias úteis", "contagem de prazo", "data de recebimento"],
}

def expand_query(query: str) -> str:
    query_lower = query.lower()
    expansions = []

    for trigger, terms in EXPANSION_MAP.items():
        if trigger in query_lower:
            expansions.extend(terms)

    if expansions:
        return f"{query} {' '.join(expansions)}"
    return query
```

A segunda ação é ajustar a estratégia de chunking para que seções de Objetivo muito curtas (menos de 60 tokens de conteúdo efetivo) sejam fundidas com a seção seguinte durante o processamento, evitando que chunks introdutórios concorram com chunks operacionais no retrieval.

---

## Sumário executivo dos problemas e correções

| #   | Problema                                             | Criticidade   | Correção principal                                        | Esforço estimado |
| --- | ---------------------------------------------------- | ------------- | --------------------------------------------------------- | ---------------- |
| 1   | FAQ informal domina ranking sobre documentos formais | 🔴 Alta       | Separação em duas coleções ChromaDB (formal/informal)     | 1–2 dias         |
| 2   | Versão obsoleta PROC-042 v1 rankeia acima da v2      | 🔴 Alta       | Filtro de penalização pós-retrieval + conflict detector   | 1 dia            |
| 3   | Tabelas Markdown têm baixa recuperabilidade          | 🟠 Média-alta | Prefixação semântica no chunking + reranker cross-encoder | 2–3 dias         |
| 4   | Seções introdutórias superam seções operacionais     | 🟡 Média      | Query expansion + fusão de chunks curtos no chunking      | 1–2 dias         |

**Sequência de implementação recomendada:** Problema 1 → Problema 2 → re-executar os 5 testes de retrieval para medir impacto → Problema 3 → Problema 4. Os dois primeiros são independentes entre si e têm maior impacto imediato sobre a confiabilidade do sistema. Os dois últimos dependem de refatoração do pipeline de chunking e devem ser acompanhados de re-indexação completa da base.
