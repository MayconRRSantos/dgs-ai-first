# Exercício 1.3 — Construção de pipeline de RAG com ferramentas open-source

## Histórico de Iteração com Claude + GitHub Copilot

### Conversas Utilizadas

- **Claude (Fase de Planejamento e Desenho):** https://claude.ai/share/0cc884d5-e10b-4bf4-b97c-885fa54e2075
- **GitHub Copilot (Implementação do Pipeline):** [Sessão no VS Code / GitHub Copilot Chat](./copilot-session-exercicio-1.3.json)
- **Claude (Avaliação e Refinamento):** https://claude.ai/share/0cc884d5-e10b-4bf4-b97c-885fa54e2075

**Iterações realizadas:**

1. Contextualização completa do exercício e geração do documento de arquitetura (`01-desenho-arquitetura-rag.md`)
2. Implementação completa das etapas de ingestão, busca e montagem de prompt usando GitHub Copilot (Tarefas 1 e 2)
3. Execução dos testes com as 5 perguntas do mapa de cobertura (Anexo B)
4. Avaliação das respostas geradas pelo Claude + análise comparativa com o gabarito
5. Identificação de problemas reais e proposição de correções (`response-evaluation.md` e `issues-and-fixes.md`)
6. Compilação final e consolidação do entregável

**Objetivo:**
Construir uma prova de conceito funcional de um pipeline de RAG utilizando apenas ferramentas gratuitas e open-source (Python + ChromaDB + sentence-transformers + LangChain), demonstrando as etapas completas de ingestão de documentos, geração de embeddings, recuperação vetorial e montagem de prompt. O foco foi validar a qualidade da recuperação antes de investir em soluções proprietárias, seguindo as diretrizes do Tech Lead.

**Ferramentas utilizadas:**

- **Claude** (para planejamento, arquitetura, avaliação crítica e refinamento)
- **GitHub Copilot** (para codificação acelerada do pipeline)
- Stack 100% open-source: Python, ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`), LangChain
