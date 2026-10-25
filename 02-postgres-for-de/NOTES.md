# NOTES — 02 Postgres for data engineers

Minhas anotações, respostas dos exercícios e o que quebrou.

## Respostas dos exercícios

### Ex 1 — índice escolhido e ordem das colunas

### Ex 2 — por que cada query ignorou o índice (a, b, c, d)

### Ex 3 — custo do REPLICA IDENTITY FULL / o que acontece se esquecer o slot

### Ex 4 — migração para tabela particionada em produção 24/7

### Ex 5 — ON CONFLICT vs MERGE vs delete+insert

## O que quebrou e como resolvi

| Data | Sintoma / erro | Causa | Solução |
|------|----------------|-------|---------|
| 2026-10-25 | `make run` logo após `make up`: "terminating connection due to administrator command" | healthcheck `pg_isready` passava durante o init (servidor temporário) | healthcheck via TCP (`-h 127.0.0.1`): o servidor do init só escuta no socket unix |

## Aprendizados / dúvidas
