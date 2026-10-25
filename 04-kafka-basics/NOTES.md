# NOTES — 04 Kafka fundamentals

Minhas anotações, respostas dos exercícios e o que quebrou.

## Respostas dos exercícios

### Ex 1 — sem key: como escolhe partição / quando usar sem key

### Ex 2 — o 7º consumer / range vs cooperative-sticky

### Ex 3 — at-most-once: o que perdi / quando cada semântica é aceitável

### Ex 5 — por que commitar só depois de escrever na DLQ

### Ex 7 — o que sobreviveu à compactação

## O que quebrou e como resolvi

| Data | Sintoma / erro | Causa | Solução |
|------|----------------|-------|---------|
| 2026-10-25 | Consumer reiniciado após crash não recebia partições e saía com `processed=0` | o membro morto mantém as partições até `session.timeout.ms` (45s padrão) | `session.timeout.ms=10000` + esperar mais no restart |
| 2026-10-25 | `Commit failed: Local: No offset stored` no fim | commit final sem nenhum offset novo desde o último commit | só commitar se houver mensagens não commitadas |

## Aprendizados / dúvidas
