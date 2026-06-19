---
name: typescript-conventions
level: foundation
activation: "ao gerar ou editar qualquer código TypeScript no projeto NovaTech Assistant"
owner: Tech Lead
consumers: [todos os devs, Copilot, Claude Code]
depends_on: []   # é a base; nenhuma dependência
---

# Skill Foundation — TypeScript Conventions (NovaTech Assistant)

## Contexto — quando aplicar

Aplique **em toda** geração/edição de código TypeScript do backend, bot e pipeline. Esta é a skill
base: as skills `error-handling`, `project-structure`, `azure-functions-endpoint`,
`testing-patterns` e todas as Artifact **pressupõem** estas regras. Não as repita nelas — referencie.

Decisões herdadas: `tsconfig` com `strict: true`, ESM (`"type": "module"`), Zod para validação,
pino para log (ADRs do cenário 1 / AGENTS.md).

## Regras prescritivas (DEVE)

1. **DEVE** compilar com `strict: true`. Zero erros em `tsc --noEmit`.
2. **DEVE** tipar explicitamente parâmetros e retorno de funções exportadas (API pública).
3. **DEVE** usar `import type { ... }` para imports que são só tipos.
4. **DEVE** usar extensão `.js` nos imports relativos (ESM/NodeNext): `from "../shared/types.js"`.
5. **DEVE** usar `interface`/`type` nomeados para shapes de domínio (nada de objetos anônimos repetidos).
6. **DEVE** modelar conjuntos fechados como **union de literais** (`type Tier = "Gold" | "Silver" | "Standard"`), não `string` nem `enum` numérico.
7. **DEVE** usar named exports. **NÃO** usar `export default`.
8. **DEVE** validar dados externos (body, env, resposta de API) com Zod antes de tipar como o domínio.
9. **DEVE** logar via `logger` (pino). **NUNCA** `console.log/err/warn`.
10. **DEVE** preferir `unknown` a `any` na borda e estreitar com type guard/Zod.

## NÃO DEVE

- `any` (explícito ou via `as any`) para silenciar o compilador.
- `// @ts-ignore` / `// @ts-expect-error` sem comentário justificando.
- `require(...)` dinâmico ou `import()` para contornar tipos.
- Asserção `as Tipo` sem validação prévia (cast cego de `unknown`).
- Mutar parâmetros de entrada; preferir dados imutáveis (`readonly`, `const`).

## DO / DON'T — código real do domínio

### Conjuntos fechados (tiers de cliente)

❌ **DON'T** — o Copilot tende a gerar isto:
```ts
function getSla(tier: string) {            // aceita "Platinum", "gold", qualquer string
  if (tier == "Gold") return "2h";         // == em vez de ===; sem exaustividade
}
```

✅ **DO**:
```ts
import type { Tier } from "../shared/types.js";

const FIRST_RESPONSE_SLA: Record<Tier, string> = {
  Gold: "2h úteis",
  Silver: "4h úteis",
  Standard: "8h úteis",
};

export function firstResponseSla(tier: Tier): string {
  return FIRST_RESPONSE_SLA[tier]; // exaustivo por construção: novo tier quebra o build
}
```

### Borda: validar antes de confiar no tipo

❌ **DON'T**:
```ts
const body = (await request.json()) as QueryRequest; // mentira de tipo: nada foi validado
```

✅ **DO**:
```ts
import { parseQueryRequest } from "./validator.js"; // Zod -> QueryRequest ou ValidationError
const query = parseQueryRequest(await request.json());
```

### Erros e logging

❌ **DON'T**:
```ts
try { /* ... */ } catch (e: any) {
  console.log("erro", e);          // console + any
  throw e;
}
```

✅ **DO**:
```ts
import { logger } from "../shared/logger.js";
import { InternalError } from "../shared/errors.js";

try { /* ... */ } catch (err) {            // err: unknown
  logger.error({ err }, "falha ao buscar chunks");
  throw new InternalError("search failed"); // não vaza detalhe de upstream ao cliente
}
```

## Anti-padrões que o Copilot gera de fato (vigie no review)

| Anti-padrão | Por que é ruim | Correção |
|-------------|----------------|----------|
| `as any` / `: any` | desliga o strict; bugs vazam em runtime | `unknown` + Zod/type guard |
| `console.log(...)` | sem nível, sem redaction, polui stdout do host | `logger.info(...)` (pino) |
| `tier: string` | aceita "Platinum" (tier inexistente) → alucinação | `tier: Tier` (union literal) |
| `export default` | dificulta refactor/auto-import consistente | named export |
| import sem `.js` | quebra em runtime ESM (compila, mas falha ao rodar) | sufixo `.js` no import relativo |
| `JSON.parse(body)` cru | aceita qualquer shape; 500 em vez de 400 | validar com Zod (`safeParse`) |
| `enum Tier { Gold }` | enum numérico/objeto pesado em runtime | `type Tier = "Gold" \| ...` |

## Dependências

Nenhuma — esta é a Foundation base. Skills que geram código (`azure-functions-endpoint`,
`testing-patterns`, `create-rag-endpoint`, …) **devem** referenciar esta skill em vez de repetir
estas regras.

## Verificação rápida (antes de aceitar código gerado)

```bash
npx tsc --noEmit -p .         # 0 erros
grep -rn "console\.\|as any\| any\b" src/   # deve voltar vazio
```
