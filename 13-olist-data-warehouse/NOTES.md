# NOTES — 13 Olist data warehouse

Minhas anotações sobre o projeto, o que eu mudaria e o que quebrou.

## Para explicar em entrevista (pitch de 2 minutos)

- Problema:
- Decisões principais (e alternativas descartadas):
- O achado de dados mais interessante:
- O que eu faria diferente em produção:

## Extensões que fiz

| Data | Extensão | O que aprendi |
|------|----------|---------------|
|      |          |               |

## O que quebrou e como resolvi

| Data | Sintoma / erro | Causa | Solução |
|------|----------------|-------|---------|
| 2026-10-25 | sqlfluff: `Invalid option '{'table': 'explicit'}'` | chave errada na config da regra aliasing | `aliasing = explicit` dentro de `[sqlfluff:rules:aliasing.table]` |
| 2026-10-25 | Streamlit avisando `use_container_width` deprecado | API mudou | `width="stretch"` |
