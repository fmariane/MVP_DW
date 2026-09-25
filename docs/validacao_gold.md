# Gold: implantação e validação

Job `465875515640680`, notebook [04_gold.py](../notebooks/04_gold.py), executado
com sucesso em 24/09/2026 às 22:55 de São Paulo (25/09 às 01:55 UTC).
As duas Silver foram lidas na versão Delta 0, com hashes registrados na evidência.

- [Evidência da carga](../evidencias/gold_700142655207447.json)
- [Evidência da reexecução](../evidencias/gold_483524129599626.json)
- [Execução no Databricks](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/465875515640680/run/700142655207447)
- [Catálogo Gold](catalogo_gold.md)
- [Guia de execução](execucao_databricks.md)

## Objetos criados em workspace.mvp_gold

| Tabela Delta | Linhas | Soma de qtde_vitimas |
| --- | ---: | ---: |
| dim_tempo | 365 | Não se aplica |
| dim_municipio | 853 | Não se aplica |
| dim_natureza_delito | 174 | Não se aplica |
| fato_violencia_domestica | 117169 | 162032 |
| fato_feminicidio | 381 | 391 |

A view `comparativo_municipio_mes` possui 9296 combinações observadas de
município, ano e mês, com uma linha por chave. É uma comparação de fontes,
não uma tabela de vítimas somadas nem um calendário municipal completo.

## Integridade e reconciliação

- Campos obrigatórios sem nulos ou texto vazio.
- Chaves de dimensão e chaves compostas das fatos únicas e não nulas.
- Calendário completo de 2025; uma chave determinística AAAAMMDD por dia.
- Nomes e atributos municipais consistentes por código após o tratamento Silver.
- Naturezas únicas e identificadas por SHA-256 do nome normalizado em UTF-8.
- Zero referências sem correspondência nas cinco relações fato–dimensão.
- Contagens e somas iguais antes/depois de cada junção, na construção e na releitura das tabelas persistidas.
- Tipos e conteúdo persistidos iguais aos candidatos, verificados com comparação nos dois sentidos e multiplicidades preservadas.
- Metadados de origem, hash e ingestão propagados às fatos; valores S/N não traduzidos.

As chaves são regras lógicas verificadas pelo pipeline. Não foram declaradas
constraints PK/FK no catálogo; não se atribui a elas enforcement automático.

## Comparação entre fontes

Cada fato é agregada por município, ano e mês antes de um FULL OUTER JOIN.
As medidas `vitimas_violencia_domestica` e `vitimas_feminicidio` permanecem
separadas. Indicadores de presença distinguem registros encontrados em cada
fonte; ausência conserva NULL, sem preenchimento automático por zero.
Cada lado da view foi comparado com sua agregação independente.

## Testes e publicação

Testes sintéticos no mesmo runtime confirmaram o bloqueio de chaves dimensionais
duplicadas e FKs órfãs, a preservação de totais numa junção válida, a codificação
SHA-256 de texto acentuado e a manutenção de municípios exclusivos e valores
nulos na comparação das fontes.

O job valida todos os candidatos e objetos existentes antes de criar tabelas.
Reexecuções validam objetos existentes; não sobrescrevem divergências nem
acrescentam linhas. Não há transação única entre as cinco tabelas e a view;
uma execução final aprovada é condição para o consumo analítico.

A reexecução `483524129599626` concluiu com `SUCCESS`. As cinco tabelas foram
validadas como snapshots existentes, mantendo IDs Delta, linhas e medidas.
A view continuou com 9296 chaves, e os controles de integridade passaram
novamente. Nenhuma linha foi acrescentada às tabelas Gold.

Itens 16 e 17 concluídos. O [catálogo completo](catalogo_dados.md) e a
[linhagem](linhagem_dados.md), item 18, também foram concluídos. Consultas,
gráficos e interpretação (19–20) concluídos no [relatório analítico](resultados_analiticos.md).
Screenshots (21) e reexecução integral da entrega (23) permanecem pendentes.
