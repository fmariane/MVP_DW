# Esquema físico extraído do Databricks

Extração UTC: 2026-09-25T02:03:20.361847+00:00.

Gerado por `scripts/catalogar_databricks.py`. Tipos e anulabilidade são metadados reais do Unity Catalog.
`nullable=true` indica permissão física para NULL; não significa que o campo está vazio ou que o contrato lógico aceite ausência.
Regras e descrições: [catálogo completo](catalogo_dados.md). Linhagem: [documento de linhagem](linhagem_dados.md).

## workspace.mvp_bronze.feminicidio_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `string` | Sim |
| 3 | mes | `string` | Sim |
| 4 | ano | `string` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | tentado_consumado | `string` | Sim |
| 8 | qtde_vitimas | `string` | Sim |
| 9 | arquivo_origem | `string` | Sim |
| 10 | arquivo_sha256 | `string` | Sim |
| 11 | ingerido_em | `timestamp` | Sim |

## workspace.mvp_bronze.violencia_domestica_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `string` | Sim |
| 3 | mes | `string` | Sim |
| 4 | ano | `string` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | natureza_delito | `string` | Sim |
| 8 | tentado_consumado | `string` | Sim |
| 9 | qtde_vitimas | `string` | Sim |
| 10 | arquivo_origem | `string` | Sim |
| 11 | arquivo_sha256 | `string` | Sim |
| 12 | ingerido_em | `timestamp` | Sim |

## workspace.mvp_silver.feminicidio_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `date` | Sim |
| 3 | mes | `int` | Sim |
| 4 | ano | `int` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | tentado_consumado | `string` | Sim |
| 8 | qtde_vitimas | `bigint` | Sim |
| 9 | dados_brutos | `struct<municipio_cod:string,municipio_fato:string,data_fato:string,mes:string,ano:string,risp:string,rmbh:string,tentado_consumado:string,qtde_vitimas:string>` | Sim |
| 10 | arquivo_origem | `string` | Sim |
| 11 | arquivo_sha256 | `string` | Sim |
| 12 | ingerido_em | `timestamp` | Sim |
| 13 | tabela_bronze | `string` | Sim |
| 14 | versao_bronze | `bigint` | Sim |
| 15 | versao_regras | `string` | Sim |
| 16 | tratado_em | `timestamp` | Sim |

## workspace.mvp_silver.rejeicoes_feminicidio_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `date` | Sim |
| 3 | mes | `int` | Sim |
| 4 | ano | `int` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | tentado_consumado | `string` | Sim |
| 8 | qtde_vitimas | `bigint` | Sim |
| 9 | dados_brutos | `struct<municipio_cod:string,municipio_fato:string,data_fato:string,mes:string,ano:string,risp:string,rmbh:string,tentado_consumado:string,qtde_vitimas:string>` | Sim |
| 10 | arquivo_origem | `string` | Sim |
| 11 | arquivo_sha256 | `string` | Sim |
| 12 | ingerido_em | `timestamp` | Sim |
| 13 | tabela_bronze | `string` | Sim |
| 14 | versao_bronze | `bigint` | Sim |
| 15 | versao_regras | `string` | Sim |
| 16 | tratado_em | `timestamp` | Sim |
| 17 | _quantidade_valida | `boolean` | Sim |
| 18 | motivos_rejeicao | `array<string>` | Sim |
| 19 | execucao_id | `string` | Sim |

## workspace.mvp_silver.rejeicoes_violencia_domestica_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `date` | Sim |
| 3 | mes | `int` | Sim |
| 4 | ano | `int` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | natureza_delito | `string` | Sim |
| 8 | tentado_consumado | `string` | Sim |
| 9 | qtde_vitimas | `bigint` | Sim |
| 10 | dados_brutos | `struct<municipio_cod:string,municipio_fato:string,data_fato:string,mes:string,ano:string,risp:string,rmbh:string,natureza_delito:string,tentado_consumado:string,qtde_vitimas:string>` | Sim |
| 11 | arquivo_origem | `string` | Sim |
| 12 | arquivo_sha256 | `string` | Sim |
| 13 | ingerido_em | `timestamp` | Sim |
| 14 | tabela_bronze | `string` | Sim |
| 15 | versao_bronze | `bigint` | Sim |
| 16 | versao_regras | `string` | Sim |
| 17 | tratado_em | `timestamp` | Sim |
| 18 | _quantidade_valida | `boolean` | Sim |
| 19 | motivos_rejeicao | `array<string>` | Sim |
| 20 | execucao_id | `string` | Sim |

## workspace.mvp_silver.violencia_domestica_2025

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_fato | `string` | Sim |
| 2 | data_fato | `date` | Sim |
| 3 | mes | `int` | Sim |
| 4 | ano | `int` | Sim |
| 5 | risp | `string` | Sim |
| 6 | rmbh | `string` | Sim |
| 7 | natureza_delito | `string` | Sim |
| 8 | tentado_consumado | `string` | Sim |
| 9 | qtde_vitimas | `bigint` | Sim |
| 10 | dados_brutos | `struct<municipio_cod:string,municipio_fato:string,data_fato:string,mes:string,ano:string,risp:string,rmbh:string,natureza_delito:string,tentado_consumado:string,qtde_vitimas:string>` | Sim |
| 11 | arquivo_origem | `string` | Sim |
| 12 | arquivo_sha256 | `string` | Sim |
| 13 | ingerido_em | `timestamp` | Sim |
| 14 | tabela_bronze | `string` | Sim |
| 15 | versao_bronze | `bigint` | Sim |
| 16 | versao_regras | `string` | Sim |
| 17 | tratado_em | `timestamp` | Sim |

## workspace.mvp_gold.comparativo_municipio_mes

Objeto: VIEW; formato: não se aplica.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | ano | `int` | Sim |
| 2 | mes | `int` | Sim |
| 3 | vitimas_violencia_domestica | `bigint` | Sim |
| 4 | presente_vitimas_violencia_domestica | `boolean` | Não |
| 5 | vitimas_feminicidio | `bigint` | Sim |
| 6 | presente_vitimas_feminicidio | `boolean` | Não |

## workspace.mvp_gold.dim_municipio

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | municipio_cod | `string` | Sim |
| 1 | municipio_nome | `string` | Sim |
| 2 | uf | `string` | Sim |
| 3 | risp_cod | `string` | Sim |
| 4 | recorte_metropolitano | `string` | Sim |

## workspace.mvp_gold.dim_natureza_delito

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | natureza_key | `string` | Sim |
| 1 | natureza_nome | `string` | Sim |

## workspace.mvp_gold.dim_tempo

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | data_key | `int` | Sim |
| 1 | data | `date` | Sim |
| 2 | ano | `int` | Sim |
| 3 | mes | `int` | Sim |
| 4 | dia | `int` | Sim |
| 5 | trimestre | `int` | Sim |

## workspace.mvp_gold.fato_feminicidio

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | data_key | `int` | Sim |
| 1 | municipio_cod | `string` | Sim |
| 2 | situacao | `string` | Sim |
| 3 | qtde_vitimas | `bigint` | Sim |
| 4 | arquivo_origem | `string` | Sim |
| 5 | arquivo_sha256 | `string` | Sim |
| 6 | ingerido_em | `timestamp` | Sim |

## workspace.mvp_gold.fato_violencia_domestica

Objeto: MANAGED; formato: DELTA.

| Posição (base 0) | Campo | Tipo físico | Permite NULL fisicamente |
| --- | --- | --- | --- |
| 0 | data_key | `int` | Sim |
| 1 | municipio_cod | `string` | Sim |
| 2 | natureza_key | `string` | Sim |
| 3 | codigo_tentado_consumado | `string` | Sim |
| 4 | qtde_vitimas | `bigint` | Sim |
| 5 | arquivo_origem | `string` | Sim |
| 6 | arquivo_sha256 | `string` | Sim |
| 7 | ingerido_em | `timestamp` | Sim |
