"""
search.py — Módulo de busca semântica para o RAG da NovaTech.

Recebe uma pergunta (string), gera o embedding correspondente,
busca os 4 chunks mais similares no ChromaDB local e retorna
uma lista com texto do chunk, documento de origem e score.
"""

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------

CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 4

# ---------------------------------------------------------------------------
# Inicialização (lazy loading para evitar recarregar em cada chamada)
# ---------------------------------------------------------------------------

_modelo = None
_collection = None


def _get_modelo() -> SentenceTransformer:
    """Carrega o modelo de embedding (singleton)."""
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer(EMBEDDING_MODEL)
    return _modelo


def _get_collection():
    """Obtém a coleção do ChromaDB (singleton)."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        try:
            _collection = client.get_collection(name=COLLECTION_NAME)
        except ValueError:
            raise RuntimeError(
                f"Coleção '{COLLECTION_NAME}' não encontrada no ChromaDB. "
                f"Execute 'python ingest.py' primeiro para indexar os documentos."
            )
    return _collection


# ---------------------------------------------------------------------------
# Função principal de busca
# ---------------------------------------------------------------------------


def buscar_chunks(pergunta: str, top_k: int = TOP_K) -> list[dict]:
    """
    Busca os chunks mais similares à pergunta no ChromaDB.

    Args:
        pergunta: Texto da pergunta do atendente.
        top_k: Número de chunks a retornar (padrão: 4).

    Returns:
        Lista de dicts com:
            - texto: conteúdo do chunk
            - fonte: nome do arquivo de origem
            - section_path: caminho hierárquico da seção
            - trust_level: nível de confiança (formal/informal)
            - version: versão do documento
            - score: score de similaridade (0 a 1, quanto maior melhor)
    """
    if not pergunta or not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")

    modelo = _get_modelo()
    collection = _get_collection()

    # Gera embedding da pergunta
    query_embedding = modelo.encode(pergunta).tolist()

    # Busca por similaridade cosseno no ChromaDB
    resultados = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Monta lista de resultados formatados
    chunks_encontrados = []

    if resultados and resultados["documents"] and resultados["documents"][0]:
        for i, texto in enumerate(resultados["documents"][0]):
            metadata = resultados["metadatas"][0][i]
            # ChromaDB retorna distância cosseno (0 = idêntico, 2 = oposto)
            # Convertemos para score de similaridade (1 = idêntico, 0 = oposto)
            distancia = resultados["distances"][0][i]
            score = 1 - (distancia / 2)

            chunks_encontrados.append(
                {
                    "texto": texto,
                    "fonte": metadata.get("source_file", "desconhecido"),
                    "section_path": metadata.get("section_path", ""),
                    "trust_level": metadata.get("trust_level", "informal"),
                    "version": metadata.get("version", "v1"),
                    "doc_type": metadata.get("doc_type", "OUTROS"),
                    "score": round(score, 4),
                }
            )

    return chunks_encontrados


# ---------------------------------------------------------------------------
# Execução standalone para testes rápidos
# ---------------------------------------------------------------------------


def main():
    """Modo interativo para testar buscas."""
    print("=" * 60)
    print("NovaTech RAG — Busca Semântica (modo interativo)")
    print("Digite 'sair' para encerrar.")
    print("=" * 60)

    while True:
        print()
        pergunta = input("Pergunta: ").strip()

        if pergunta.lower() in ("sair", "exit", "quit"):
            print("Encerrando.")
            break

        if not pergunta:
            continue

        try:
            resultados = buscar_chunks(pergunta)
        except RuntimeError as e:
            print(f"\n[ERRO] {e}")
            break

        if not resultados:
            print("\n  Nenhum chunk relevante encontrado.")
            continue

        print(f"\n  Top {len(resultados)} chunks encontrados:\n")
        for i, chunk in enumerate(resultados, 1):
            print(f"  --- Resultado {i} (score: {chunk['score']}) ---")
            print(f"  Fonte: {chunk['fonte']} ({chunk['trust_level']})")
            print(f"  Seção: {chunk['section_path']}")
            print(f"  Texto: {chunk['texto'][:200]}...")
            print()


if __name__ == "__main__":
    main()
