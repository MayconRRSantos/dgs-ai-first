"""
ingest.py — Pipeline de ingestão para o RAG da NovaTech.

Lê arquivos .md da pasta documentos/, aplica chunking hierárquico por
cabeçalhos Markdown, gera embeddings com all-MiniLM-L6-v2 e persiste
no ChromaDB local (./chroma_db).
"""

import os
import hashlib
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------

DOCUMENTOS_DIR = Path("documentos")
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Cabeçalhos Markdown para split hierárquico
HEADERS_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------


def gerar_doc_id(conteudo: str) -> str:
    """Gera um identificador único baseado no hash SHA-256 do conteúdo."""
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def detectar_trust_level(nome_arquivo: str) -> str:
    """
    Classifica o nível de confiança do documento com base no nome.
    Documentos POL, PROC e SLA são formais; FAQ e outros são informais.
    """
    nome_upper = nome_arquivo.upper()
    if any(prefix in nome_upper for prefix in ["POL-", "PROC-", "SLA-"]):
        return "formal"
    return "informal"


def detectar_doc_type(nome_arquivo: str) -> str:
    """Extrai o tipo do documento a partir do prefixo do nome do arquivo."""
    nome_upper = nome_arquivo.upper()
    for prefix in ["POL", "PROC", "SLA", "FAQ"]:
        if nome_upper.startswith(prefix):
            return prefix
    return "OUTROS"


def detectar_versao(nome_arquivo: str) -> str:
    """Tenta extrair a versão do nome do arquivo (ex: v1, v2)."""
    match = re.search(r"v(\d+)", nome_arquivo.lower())
    if match:
        return f"v{match.group(1)}"
    return "v1"


def construir_section_path(metadata_headers: dict) -> str:
    """
    Constrói o caminho hierárquico da seção a partir dos metadados
    gerados pelo MarkdownHeaderTextSplitter.
    """
    parts = []
    for level in ["h1", "h2", "h3", "h4"]:
        if level in metadata_headers:
            parts.append(metadata_headers[level])
    return " > ".join(parts) if parts else "Raiz do documento"


def carregar_documentos(diretorio: Path) -> list[dict]:
    """
    Carrega todos os arquivos .md do diretório especificado.
    Retorna lista de dicts com nome, conteúdo e metadados básicos.
    """
    documentos = []

    if not diretorio.exists():
        raise FileNotFoundError(
            f"Diretório '{diretorio}' não encontrado. "
            f"Crie a pasta e adicione os arquivos .md antes de executar."
        )

    arquivos_md = list(diretorio.glob("*.md"))

    if not arquivos_md:
        raise ValueError(
            f"Nenhum arquivo .md encontrado em '{diretorio}'. "
            f"Adicione os documentos antes de executar a ingestão."
        )

    for arquivo in arquivos_md:
        conteudo = arquivo.read_text(encoding="utf-8")
        documentos.append(
            {
                "nome": arquivo.name,
                "conteudo": conteudo,
                "trust_level": detectar_trust_level(arquivo.name),
                "doc_type": detectar_doc_type(arquivo.name),
                "version": detectar_versao(arquivo.name),
            }
        )
        print(f"  [OK] Carregado: {arquivo.name} ({len(conteudo)} chars)")

    return documentos


def chunkar_documento(documento: dict) -> list[dict]:
    """
    Aplica chunking hierárquico por cabeçalhos Markdown.
    Cada chunk herda o contexto dos cabeçalhos pai (section_path).
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT,
        strip_headers=False,
    )

    splits = splitter.split_text(documento["conteudo"])
    chunks = []

    for i, split in enumerate(splits):
        section_path = construir_section_path(split.metadata)

        # Prefixo de contexto hierárquico embutido no texto do chunk
        contexto_prefix = f"[{documento['nome']} | {section_path}]\n\n"
        texto_chunk = contexto_prefix + split.page_content

        chunk_id = gerar_doc_id(f"{documento['nome']}_{i}_{texto_chunk}")

        chunks.append(
            {
                "id": chunk_id,
                "texto": texto_chunk,
                "metadata": {
                    "source_file": documento["nome"],
                    "doc_type": documento["doc_type"],
                    "section_path": section_path,
                    "version": documento["version"],
                    "trust_level": documento["trust_level"],
                    "chunk_index": i,
                },
            }
        )

    return chunks


def gerar_embeddings(chunks: list[dict], modelo: SentenceTransformer) -> list[list[float]]:
    """Gera embeddings para todos os chunks em batch."""
    textos = [chunk["texto"] for chunk in chunks]
    embeddings = modelo.encode(textos, show_progress_bar=True, batch_size=64)
    return embeddings.tolist()


def indexar_no_chromadb(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Persiste chunks e embeddings no ChromaDB local."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Recria a coleção para garantir ingestão limpa
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass  # Coleção não existia

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Prepara dados para upsert em batch
    ids = [chunk["id"] for chunk in chunks]
    documentos = [chunk["texto"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    # ChromaDB suporta upsert em batch
    BATCH_SIZE = 100
    for start in range(0, len(ids), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.upsert(
            ids=ids[start:end],
            documents=documentos[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    print(f"  [OK] {len(ids)} chunks indexados na coleção '{COLLECTION_NAME}'")


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def main():
    """Executa o pipeline completo de ingestão."""
    print("=" * 60)
    print("NovaTech RAG — Pipeline de Ingestão")
    print("=" * 60)

    # 1. Carregar documentos
    print("\n[1/4] Carregando documentos...")
    documentos = carregar_documentos(DOCUMENTOS_DIR)
    print(f"       Total: {len(documentos)} documentos carregados.")

    # 2. Chunking hierárquico
    print("\n[2/4] Aplicando chunking hierárquico por cabeçalhos...")
    todos_chunks = []
    for doc in documentos:
        chunks_doc = chunkar_documento(doc)
        todos_chunks.extend(chunks_doc)
        print(f"  [OK] {doc['nome']}: {len(chunks_doc)} chunks gerados")
    print(f"       Total: {len(todos_chunks)} chunks.")

    # 3. Gerar embeddings
    print(f"\n[3/4] Gerando embeddings com '{EMBEDDING_MODEL}'...")
    modelo = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = gerar_embeddings(todos_chunks, modelo)
    print(f"       {len(embeddings)} embeddings gerados (dim={len(embeddings[0])}).")

    # 4. Indexar no ChromaDB
    print("\n[4/4] Indexando no ChromaDB...")
    indexar_no_chromadb(todos_chunks, embeddings)

    print("\n" + "=" * 60)
    print("Ingestão concluída com sucesso!")
    print(f"  - Documentos processados: {len(documentos)}")
    print(f"  - Chunks indexados: {len(todos_chunks)}")
    print(f"  - Persistência: {CHROMA_PERSIST_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
