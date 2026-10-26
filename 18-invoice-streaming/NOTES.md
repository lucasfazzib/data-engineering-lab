# Notes

## O que quebrou e como resolvi

| Problema | Causa | Correção |
|---|---|---|
| MongoDB com menos itens (4.938) do que linhas enviadas (5.017) | 79 linhas duplicadas exatas na fonte; `$addToSet` junta | documentado como decisão de modelagem (README → Data) |
| Spark baixando o conector Kafka a cada start | `--packages` resolve no runtime | jars copiados para `/opt/spark/jars` no build da imagem |
| Checkpoint sem permissão | volume nomeado criado como root | `/checkpoints` criado com dono `spark` na imagem |
| ruff B008 (`Depends` como default) | estilo antigo do FastAPI | `Annotated[Producer, Depends(...)]` |
| C: lotado durante o build | imagens + build cache do Docker no SSD | disco do Docker movido para `D:\Docker` |

## Medições (amostra padrão: 300 invoices)

- 5.017 linhas enviadas em ~13 s (~400 linhas/s pelo client, 1 request por linha).
- Spark: 4 micro-batches, ~1 s por batch; `spark-output` com os mesmos 5.017 registros.
- Reenvio do dataset inteiro: MongoDB continua com 300 invoices / 4.938 itens (idempotente).
