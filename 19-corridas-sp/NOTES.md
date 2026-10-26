# Notes

## Decisões tomadas no caminho

| Situação | Decisão |
|---|---|
| Ticket Sports: robots.txt permite, mas os termos proíbem reproduzir conteúdo | fora; termos de uso também contam, não só o robots.txt |
| Nominatim: robots.txt bloqueia `/search` | fora; centróides dos municípios vêm da API de malhas do IBGE (1 requisição) |
| IBGE: robots.txt responde 503 | API pública documentada → `get_api()` (robots.txt é para crawlers de páginas) |
| Página da CBAt tem aba de atletas | parser lê só o cabeçalho; bronze guarda campos + hash, nunca o HTML |
| Página de evento da Minhas Inscrições tem e-mail do organizador no meio do texto | só números/flags saem da página; teste garante que nenhum texto vaza |
| Link do card passa por contador de cliques | redirect resolvido 1x por evento, sem seguir, e cacheado |
| Mesma prova listada como "- Pix" e "- Cartão" | normalização do nome + ER; nome exibido sem o sufixo |
| CBAt quase não tem corrida de rua de SP | mantida (oficial, grandes provas); a cobertura vem da Minhas Inscrições |

## O que quebrou e como resolvi

| Problema | Causa | Correção |
|---|---|---|
| `vars` com `env_var` não expandia no `external_location` | valor de `vars` não é renderizado de novo | `env_var` direto no `_sources.yml` |
| Teste de robots 503 demorava 76 s | backoff real no retry | `time.sleep` mockado no teste |
