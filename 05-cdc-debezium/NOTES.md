# NOTES — 05 CDC with Debezium

Minhas anotações, respostas dos exercícios e o que quebrou.

## Respostas dos exercícios

### Ex 1 — connector parado / deletado: o que acontece com o slot

### Ex 3 — por que outbox é mais seguro que publicar no Kafka pela aplicação

### Ex 4 — mudança de schema e o downstream

### Ex 6 — quando usar incremental snapshot

## O que quebrou e como resolvi

| Data | Sintoma / erro | Causa | Solução |
|------|----------------|-------|---------|
| 2026-10-25 | `GET /connectors/<name>/status -> 404` logo após registrar | o status leva alguns segundos para existir após o PUT | tratar 404 como "ainda não" e tentar de novo |

## Aprendizados / dúvidas
