# Silver: implementação e reconciliação

Implementada no Databricks Free Edition pelo notebook [03_silver.py](../notebooks/03_silver.py),
com regras `silver_v1`. Job serverless `1075813885223029`, sem agendamento.
Primeira carga aprovada em 24/09/2026 às 22:34 de São Paulo (25/09 às 01:34 UTC).

- [Evidência da carga](../evidencias/silver_169682925174743.json)
- [Evidência da reexecução](../evidencias/silver_572585419270618.json)
- [Execução no Databricks](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/1075813885223029/run/169682925174743)
- [Regras de tratamento](regras_silver.md)
- [Comandos de execução pelo WSL](execucao_databricks.md)

## Reconciliação comprovada

| Fonte | Linhas Bronze | Linhas rejeitadas | Linhas Silver | Soma Bronze | Soma Silver |
| --- | ---: | ---: | ---: | ---: | ---: |
| Violência doméstica | 117169 | 0 | 117169 | 162032 | 162032 |
| Feminicídio | 381 | 0 | 381 | 391 | 391 |

Leituras fixadas na versão Delta 0 de cada Bronze. Zero quantidades inválidas,
zero conflitos geográficos após a regra municipal e zero chaves operacionais
duplicadas nas tabelas publicadas. Nenhuma linha descartada, deduplicada ou
agregada. Os quantitativos permanecem separados por fonte.

Tabelas de negócio criadas:

- `workspace.mvp_silver.violencia_domestica_2025`
- `workspace.mvp_silver.feminicidio_2025`

Tabelas de auditoria criadas, vazias nesta execução:

- `workspace.mvp_silver.rejeicoes_violencia_domestica_2025`
- `workspace.mvp_silver.rejeicoes_feminicidio_2025`

Rejeições futuras conservam o registro, os motivos e o `execucao_id`. Uma linha
com vários motivos é contabilizada uma vez na reconciliação. Todas as linhas
de grupos duplicados são rejeitadas; não se escolhe uma para manter.

## Transformações e preservação

`data_fato` foi convertido para DATE, `mes` e `ano` para INT e `qtde_vitimas`
para BIGINT. Códigos municipais e RISP permanecem STRING. Tipos persistidos
foram confrontados com o contrato após a gravação.

O nome `SANTO ANT DO AMPARO`, código `315990`, foi convertido para
`SANTO ANTONIO DO AMPARO` em 109 registros de violência doméstica. Nenhum outro
campo apresentou diferença textual ao comparar sua representação tratada com
o original. As categorias S/N e TENTADO/CONSUMADO foram mantidas separadas.

Todos os campos de origem estão preservados no STRUCT `dados_brutos`. A comparação
nos dois sentidos por `exceptAll` comprovou igualdade com a Bronze, incluindo
multiplicidades. SHA-256, caminho do arquivo, timestamp de ingestão, tabela e
versão Bronze, versão das regras e timestamp do tratamento compõem a linhagem.

## Testes e publicação

Os testes sintéticos passaram no mesmo runtime. Cobriram correção municipal,
preservação do valor bruto, maiúsculas, tipagem, data impossível, código nulo,
quantidade fracionada, overflow e colisão de chave após trim. A reconciliação
sintética demonstrou a separação de cinco entradas em uma candidata e quatro
rejeitadas, distinguindo quantidades válidas e inválidas.

Os controles de ambas as fontes são avaliados antes de criar tabelas de negócio.
A publicação é individual por tabela Delta, sem transação entre as duas. Se houver
falha de infraestrutura entre as gravações, a reexecução pode completar a ausente.
Uma tabela existente deve corresponder integralmente ao candidato, exceto pelo
instante técnico de tratamento; divergências bloqueiam o job, sem sobrescrita.

A reexecução `572585419270618` também terminou com `SUCCESS`: ambas as tabelas
registraram `snapshot_existente_validado`, conservaram os mesmos IDs Delta,
linhas e somas, com zero rejeições e zero duplicatas. Nenhuma nova linha foi
inserida nas tabelas de negócio.

## Próxima etapa

Itens 14 e 15 concluídos. Faltam implementar dimensões e fatos Gold e validar
chaves, relacionamentos e totais (16–17). A reexecução integral de Bronze até
análises (23) depende dessas etapas. S/N continua sem tradução oficial.
