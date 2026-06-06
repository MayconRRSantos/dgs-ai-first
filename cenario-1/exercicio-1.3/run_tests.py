"""Script de teste de retrieval para as 5 perguntas do exercício."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from search import buscar_chunks

perguntas = [
    "Qual o prazo de devolução para carga padrão?",
    "Qual o multiplicador de frete para região Norte?",
    "Qual o SLA de atendimento para cliente Gold?",
    "Como funciona o frete para cargas acima de 500kg?",
    "Posso devolver carga perigosa?",
]

for i, p in enumerate(perguntas, 1):
    print(f"=== PERGUNTA {i}: {p} ===")
    resultados = buscar_chunks(p)
    for j, r in enumerate(resultados, 1):
        texto_limpo = r["texto"].split("]\n\n", 1)[-1] if "]\n\n" in r["texto"] else r["texto"]
        print(f"  [{j}] Score: {r['score']}")
        print(f"      Fonte: {r['fonte']} ({r['trust_level']})")
        print(f"      Secao: {r['section_path']}")
        print(f"      Texto: {texto_limpo[:300]}")
        print()
    print()
