"""
prompt_builder.py — Montagem do prompt final para o RAG da NovaTech.

Importa a função de busca semântica, recebe uma pergunta do usuário,
monta um System Prompt focado em atendimento ao cliente de logística,
concatena os chunks recuperados (com indicação de fonte) e a pergunta
em uma string pronta para ser copiada e colada em um LLM.
"""

from search import buscar_chunks

# ---------------------------------------------------------------------------
# System Prompt para atendimento logístico
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Você é um assistente especializado em atendimento ao cliente da NovaTech Logística.

REGRAS OBRIGATÓRIAS:
1. Responda APENAS com base nos trechos de documentação fornecidos abaixo.
2. Se a informação não estiver nos trechos, diga claramente: "Não encontrei cobertura para essa questão na documentação disponível. Recomendo escalar para [área responsável]."
3. NUNCA invente informações ou extrapole além do que está nos trechos.
4. NUNCA misture informações de versões diferentes de um mesmo documento sem avisar.
5. Cite a fonte de cada informação entre colchetes: [FONTE: nome_do_arquivo | seção].
6. Se houver versões conflitantes de um documento nos trechos, apresente ambas as versões e indique qual é a mais recente.
7. Se um trecho vier de fonte INFORMAL, sinalize: "⚠️ Esta informação vem de fonte informal (não validada oficialmente)."
8. Seja objetivo e direto. Priorize respostas acionáveis para o atendente."""


# ---------------------------------------------------------------------------
# Funções de montagem
# ---------------------------------------------------------------------------


def formatar_chunk(chunk: dict, indice: int) -> str:
    """
    Formata um chunk recuperado para inclusão no prompt,
    com indicação clara de fonte e confiabilidade.
    """
    confiabilidade = "FORMAL" if chunk["trust_level"] == "formal" else "⚠️ INFORMAL"

    bloco = (
        f"─── Trecho {indice} ───\n"
        f"📄 Fonte: {chunk['fonte']} (versão: {chunk['version']})\n"
        f"📍 Seção: {chunk['section_path']}\n"
        f"🔒 Confiabilidade: {confiabilidade}\n"
        f"📊 Relevância: {chunk['score']}\n"
        f"\n{chunk['texto']}\n"
    )
    return bloco


def detectar_conflitos(chunks: list[dict]) -> str | None:
    """
    Verifica se há chunks de versões diferentes do mesmo documento.
    Retorna um aviso se conflito detectado, None caso contrário.
    """
    docs_versoes = {}
    for chunk in chunks:
        # Agrupa por documento base (sem versão)
        nome_base = chunk["fonte"].split("-v")[0] if "-v" in chunk["fonte"] else chunk["fonte"]
        if nome_base not in docs_versoes:
            docs_versoes[nome_base] = set()
        docs_versoes[nome_base].add(chunk["version"])

    conflitos = []
    for doc, versoes in docs_versoes.items():
        if len(versoes) > 1:
            conflitos.append(f"{doc} (versões: {', '.join(sorted(versoes))})")

    if conflitos:
        return (
            "⚠️ ATENÇÃO: Foram recuperadas versões conflitantes dos seguintes documentos: "
            + "; ".join(conflitos)
            + ". Apresente as duas versões e indique qual é a mais recente."
        )
    return None


def montar_prompt(pergunta: str, top_k: int = 4) -> str:
    """
    Monta o prompt completo pronto para uso em um LLM.

    Args:
        pergunta: Pergunta do atendente/usuário.
        top_k: Número de chunks a recuperar.

    Returns:
        String formatada com System Prompt + Contexto + Pergunta.
    """
    if not pergunta or not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")

    # Busca chunks relevantes
    chunks = buscar_chunks(pergunta, top_k=top_k)

    # Monta seção de contexto
    if chunks:
        blocos_contexto = []
        for i, chunk in enumerate(chunks, 1):
            blocos_contexto.append(formatar_chunk(chunk, i))
        contexto_formatado = "\n".join(blocos_contexto)
    else:
        contexto_formatado = (
            "(Nenhum trecho relevante encontrado na base de documentos.)"
        )

    # Detecta conflitos de versão
    aviso_conflito = detectar_conflitos(chunks) if chunks else None

    # Monta o prompt final
    prompt_partes = [
        "=" * 70,
        "SYSTEM PROMPT",
        "=" * 70,
        SYSTEM_PROMPT,
        "",
        "=" * 70,
        "CONTEXTO RECUPERADO (BASE DE CONHECIMENTO)",
        "=" * 70,
    ]

    if aviso_conflito:
        prompt_partes.append(f"\n{aviso_conflito}\n")

    prompt_partes.extend(
        [
            contexto_formatado,
            "",
            "=" * 70,
            "PERGUNTA DO ATENDENTE",
            "=" * 70,
            pergunta,
            "",
            "=" * 70,
            "RESPOSTA",
            "=" * 70,
        ]
    )

    return "\n".join(prompt_partes)


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------


def main():
    """Modo interativo: monta prompts a partir de perguntas do usuário."""
    print("=" * 70)
    print("NovaTech RAG — Montagem de Prompt para LLM")
    print("Digite sua pergunta e receba o prompt completo pronto para copiar.")
    print("Digite 'sair' para encerrar.")
    print("=" * 70)

    while True:
        print()
        pergunta = input("📝 Pergunta do atendente: ").strip()

        if pergunta.lower() in ("sair", "exit", "quit"):
            print("Encerrando.")
            break

        if not pergunta:
            continue

        try:
            prompt_final = montar_prompt(pergunta)
        except RuntimeError as e:
            print(f"\n[ERRO] {e}")
            break
        except ValueError as e:
            print(f"\n[ERRO] {e}")
            continue

        print("\n" + "─" * 70)
        print("PROMPT GERADO (copie abaixo):")
        print("─" * 70)
        print(prompt_final)
        print("─" * 70)
        print(f"\n✅ Prompt pronto ({len(prompt_final)} caracteres). Cole no LLM.")


if __name__ == "__main__":
    main()
