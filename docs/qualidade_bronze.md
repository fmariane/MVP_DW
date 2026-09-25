# Diagnóstico de qualidade da Bronze

Executado no Databricks Free Edition em 24/09/2026, às 22:20 no horário de
São Paulo (25/09 às 01:20 UTC), por job serverless `1005669937621880`.
Execução `183810729128831`, tarefa `66854634334120`, estado `SUCCESS`.

- [Evidência completa](../evidencias/qualidade_183810729128831.json)
- [Notebook executado](../notebooks/02_qualidade.py)
- [Regras da Silver](regras_silver.md)
- [Execução no Databricks](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/1005669937621880/run/183810729128831)

## Resultado

As duas tabelas foram lidas na versão Delta 0, com hashes correspondentes aos
snapshots da Bronze. Não foram encontrados bloqueios estruturais para avançar
à implementação da Silver com as regras documentadas.

| Controle | Violência doméstica | Feminicídio |
| --- | ---: | ---: |
| Linhas | 117169 | 381 |
| Soma de qtde_vitimas | 162032 | 391 |
| Linhas com qualquer erro nas regras | 0 | 0 |
| Campos ausentes, vazios ou apenas espaços | 0 | 0 |
| Datas inválidas ou fora de 2025 | 0 | 0 |
| Incoerências entre data, mês e ano | 0 | 0 |
| Códigos municipais fora do formato do recorte | 0 | 0 |
| RISP, RMBH ou situação fora do domínio | 0 | 0 |
| Quantidades inválidas, zero ou negativas | 0 | 0 |
| Linhas integralmente duplicadas (excedentes) | 0 | 0 |
| Chaves compostas duplicadas, antes/depois da normalização | 0 / 0 | 0 / 0 |
| Campos com espaços externos detectados por trim | 0 | 0 |
| Metadados ausentes ou hash divergente | 0 | 0 |
| Meses presentes | 12 | 12 |
| Municípios presentes | 853 | 183 |
| Quantidade mínima / máxima por linha | 1 / 31 | 1 / 2 |

Ambas abrangem datas de 01/01/2025 a 31/12/2025. A evidência inclui o inventário
de categorias, contagens e somas por mês, RISP, RMBH e situação. A violência
doméstica possui 174 naturezas; os totais S/N são 161004/1028. Feminicídio:
178 consumados e 213 tentados, medidos pela soma de `qtde_vitimas`.

## Divergência municipal e correção proposta

Não há conflitos geográficos internos por fonte. Entre as fontes, há um código
com dois nomes: `315990`, `SANTO ANT DO AMPARO` e `SANTO ANTONIO DO AMPARO`.
RISP e RMBH coincidem. A simulação da correspondência explícita para o nome
completo resulta em zero conflitos na união dos 853 municípios.

O diagnóstico remoto e a releitura dos CSVs locais não identificaram espaço
externo nesses nomes. A anotação anterior da modelagem sobre espaço externo foi
corrigida. A regra de trim permanece preventiva, sem alteração observada neste
snapshot. A normalização foi apenas simulada; não foram gravadas tabelas Silver.

## Validação dos controles

Os testes sintéticos rodaram no mesmo runtime Spark antes do diagnóstico e
passaram. Exercitaram registro válido, data impossível, data fora do recorte,
incoerência de mês, código nulo ou com tamanho errado, nome vazio, categoria
inesperada, RISP/RMBH inválidas, quantidade fracionada, zero e overflow de BIGINT.
Também verificaram duplicatas brutas e colisões criadas pela remoção de espaços.
Esses registros foram usados apenas em memória, sem inserção nas fontes.

## Limitações e próximos passos

O formato dos códigos municipais foi validado; sua correspondência com um
cadastro externo não foi comprovada. S/N mantém semântica pendente e não será
traduzido. As medidas não representam pessoas distintas e as fontes não devem
ser somadas. Cobertura mensal e consistência não demonstram ausência de
subnotificação.

Itens 10 e 13 concluídos. Próximos: implementar a Silver (14) e reconciliar
entrada, rejeições e saída (15). Screenshots de entrega permanecem pendentes
no item 21.
