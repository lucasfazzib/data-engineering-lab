# Notes

## O que quebrou e como resolvi

| Problema | Causa | Correção |
|---|---|---|
| `br-...-r.json` 404 | o arquivo "simplificado" não existe no 2º turno de 2026 | usar o arquivo `-u.json` |
| `pytz` faltando ao ler timestamps | DuckDB precisa de `pytz` para devolver `timestamptz` ao Python | adicionado ao `requirements.txt` |
| `Connection reset by peer` em alguns estados | servidor do TSE sob pico de acesso | erro isolado por estado; tenta de novo no próximo ciclo |
| Totais dos estados ≠ total nacional | cada arquivo é publicado em um momento diferente | documentado; a projeção usa só os arquivos estaduais |

## Ideias para depois

- Comparar com o 2º turno de 2022 (dados abertos do TSE).
- Compactar os Parquet por hora.
