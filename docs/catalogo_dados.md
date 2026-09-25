# Catálogo de dados — MVP PCMG, MG, 2025

Catálogo completo dos objetos implementados em `workspace`, com descrições,
tipos, domínios, granularidade e origem. O [esquema físico](esquema_fisico.md)
foi extraído do Unity Catalog pela CLI; a [evidência JSON](../evidencias/catalogo_databricks.json)
preserva tipos, posições, anulabilidade física e definição da view.
A [linhagem](linhagem_dados.md) conecta arquivos, notebooks, versões e campos.

## Inventário e granularidade

As quantidades abaixo correspondem às execuções aprovadas referenciadas na
linhagem. A extração de metadados não recalcula contagens de linhas.

| Objeto | Tipo | Granularidade | Linhas aprovadas |
| --- | --- | --- | ---: |
| workspace.mvp_bronze.violencia_domestica_2025 | Tabela Delta | Uma linha do CSV doméstico, sem reagrupamento | 117169 |
| workspace.mvp_bronze.feminicidio_2025 | Tabela Delta | Uma linha do CSV de feminicídio | 381 |
| workspace.mvp_silver.violencia_domestica_2025 | Tabela Delta | Município + dia + natureza + código S/N | 117169 |
| workspace.mvp_silver.feminicidio_2025 | Tabela Delta | Município + dia + situação | 381 |
| workspace.mvp_silver.rejeicoes_violencia_domestica_2025 | Tabela Delta | Uma linha rejeitada por execução, com todos os motivos | 0 |
| workspace.mvp_silver.rejeicoes_feminicidio_2025 | Tabela Delta | Uma linha rejeitada por execução, com todos os motivos | 0 |
| workspace.mvp_gold.dim_tempo | Tabela Delta | Um dia do calendário completo de 2025 | 365 |
| workspace.mvp_gold.dim_municipio | Tabela Delta | Um código municipal publicado | 853 |
| workspace.mvp_gold.dim_natureza_delito | Tabela Delta | Uma natureza normalizada da base doméstica | 174 |
| workspace.mvp_gold.fato_violencia_domestica | Tabela Delta | Município + dia + natureza + código S/N | 117169 |
| workspace.mvp_gold.fato_feminicidio | Tabela Delta | Município + dia + situação | 381 |
| workspace.mvp_gold.comparativo_municipio_mes | View | Município + ano + mês observado em ao menos uma fonte | 9296 |

Além desses 12 objetos, o volume `workspace.mvp_bronze.arquivos` armazena os CSVs
originais e as cópias por SHA-256. Caminho: `/Volumes/workspace/mvp_bronze/arquivos`.
Não é uma tabela. Os nomes reais, tipos físicos e identificação do volume constam
na evidência de extração.

Uma linha das fontes não equivale necessariamente a uma ocorrência ou mulher
única. Os campos identificam grupos publicados, sem identificador de pessoa.
Não se presume independência entre os conjuntos para somar vítimas das fontes.

## Campos publicados: Bronze e Silver

Os campos de negócio da Bronze são STRING e preservam o texto lido do CSV.
Os nomes abaixo existem nas duas fontes, exceto `natureza_delito`, exclusiva
da violência doméstica. A Silver mantém o nome do campo e aplica o tratamento
descrito, conservando também o original em `dados_brutos`.

| Campo | Tipo Bronze → Silver | Descrição e domínio | Origem / tratamento |
| --- | --- | --- | --- |
| municipio_cod | STRING → STRING | Código publicado de seis dígitos, prefixo 31 no recorte MG | CSV homônimo; trim, sem completar dígito nem converter para número |
| municipio_fato | STRING → STRING | Nome municipal não vazio | CSV; trim e regra explícita 315990 para SANTO ANTONIO DO AMPARO |
| data_fato | STRING → DATE | Data publicada válida, 2025-01-01 a 2025-12-31 | CSV em AAAA-MM-DD; conversão sem imputação |
| mes | STRING → INT | 1–12, consistente com data_fato | CSV; conversão validada, sem substituir divergências |
| ano | STRING → INT | 2025, consistente com data_fato | CSV; conversão validada |
| risp | STRING → STRING | Código RISP 1–19; nomes regionais não fornecidos | CSV; trim e validação de inteiro, preservando código textual |
| rmbh | STRING → STRING | Belo Horizonte; RMBH (Sem BH); Interior de MG | CSV; trim; recorte categórico, não booleano |
| natureza_delito | STRING → STRING | 174 naturezas observadas na doméstica | CSV doméstico; upper(trim), preservando acentos e espaços internos |
| tentado_consumado | STRING → STRING | Doméstica: S/N, sem tradução oficial. Feminicídio: TENTADO/CONSUMADO | CSV de cada fonte; trim e maiúsculas, sem harmonizar domínios |
| qtde_vitimas | STRING → BIGINT | Quantitativo publicado positivo; observado 1–31 na doméstica e 1–2 no feminicídio | CSV; exigir dígitos, conversão sem fração/overflow, zero ou negativo |

Inventários completos de natureza, RISP, RMBH e situação, com contagens e somas:
[domínios observados](dominios_observados.md). Os limites observados são referências
destes hashes, não tetos permanentes. Novos domínios ou revisões exigem avaliação.

## Metadados Bronze e sua propagação

| Campo | Tipo | Significado / origem | Domínio lógico |
| --- | --- | --- | --- |
| arquivo_origem | STRING | Caminho absoluto da cópia preservada no volume, `snapshots/<sha256>/<arquivo>.csv` | Não vazio; propagado Bronze → Silver → fato Gold |
| arquivo_sha256 | STRING | SHA-256 calculado dos bytes originais | 64 caracteres hexadecimais; hash esperado por fonte |
| ingerido_em | TIMESTAMP | Instante de gravação da Bronze, sessão em UTC | Obrigatório; propagado, sem trocar pela data de transformação |

Cada uma das duas Bronze contém seus campos publicados mais esses três metadados.
O snapshot atual não recebe append em reexecuções; conteúdo diferente bloqueia
a carga, exigindo tratamento explícito de revisão da fonte.

## Campos adicionais da Silver

| Campo | Tipo | Descrição / origem | Regra |
| --- | --- | --- | --- |
| dados_brutos | STRUCT | Todos os campos publicados da respectiva Bronze, como STRING | Mesmo nome e valor de cada campo original; estrutura exata no esquema físico |
| tabela_bronze | STRING | Nome completo da tabela que originou a linha | workspace.mvp_bronze + nome da fonte |
| versao_bronze | BIGINT | Versão Delta fixada na leitura | 0 nas execuções aprovadas; não é ano nem versão do arquivo |
| versao_regras | STRING | Identificador do contrato de transformação | silver_v1 |
| tratado_em | TIMESTAMP | Instante do tratamento em UTC | Obrigatório; a reexecução validada preserva a tabela existente |

Cada tabela de negócio Silver contém: campos publicados tratados + `dados_brutos`
+ os três metadados Bronze + os quatro campos técnicos de origem/versão/tempo
acima. A estrutura `dados_brutos` tem dez subcampos na doméstica e nove no
feminicídio, com as descrições do dicionário de campos publicados. Nenhum valor
bruto é usado como identificação de pessoa.

## Tabelas de rejeições

Cada tabela de rejeições possui os mesmos campos da respectiva Silver, acrescidos
dos três campos abaixo. Como contém candidatos inválidos, datas ou números tratados
podem estar nulos; o texto original permanece no STRUCT. Não deve alimentar fatos.

| Campo | Tipo | Descrição / origem |
| --- | --- | --- |
| _quantidade_valida | BOOLEAN | Resultado da validação lexical, capacidade BIGINT e valor positivo da quantidade; permite reconciliar separadamente valores inválidos |
| motivos_rejeicao | ARRAY<STRING> | Todos os motivos detectados na mesma linha; sem criar uma linha por motivo |
| execucao_id | STRING | UUID da execução Silver que registrou a rejeição |

Domínio implementado de motivos:

- `ausente__<campo>` para qualquer campo publicado obrigatório.
- `data_invalida`, `data_fora_2025`, `mes_invalido`, `ano_invalido`, `data_mes_ano_incoerentes`.
- `municipio_invalido`, `risp_invalida`, `rmbh_invalida`, `categoria_invalida`.
- `quantidade_invalida`, `metadados_invalidos`.
- `duplicata_integral_bruta`, `chave_operacional_duplicada`, `conflito_geografico`.

Todas as linhas de um grupo duplicado são registradas e bloqueiam a publicação.
Reexecuções com rejeições podem registrar novamente o mesmo conteúdo sob outro
UUID: isso é histórico de tentativas, não nova violência. Sem rejeições não há
linhas para a execução; a evidência JSON registra o zero e o UUID.

## Gold e relações

O [dicionário Gold](catalogo_gold.md) descreve todos os campos das três dimensões,
duas fatos e view. Tipos foram confrontados com a extração física. Relacionamentos:

| Origem | Destino | Cardinalidade esperada |
| --- | --- | --- |
| fato_violencia_domestica.data_key | dim_tempo.data_key | Muitos para um |
| fato_feminicidio.data_key | dim_tempo.data_key | Muitos para um |
| fato_violencia_domestica.municipio_cod | dim_municipio.municipio_cod | Muitos para um |
| fato_feminicidio.municipio_cod | dim_municipio.municipio_cod | Muitos para um |
| fato_violencia_domestica.natureza_key | dim_natureza_delito.natureza_key | Muitos para um |

Na view comparativa, medidas são anuláveis quando a fonte não possui registros
na chave; flags de presença distinguem esse caso. Os dois lados são agregados
antes da junção, sem soma entre as fontes.

## Obrigatoriedade, qualidade e limitações

`nullable` no [esquema físico](esquema_fisico.md) é permissão de armazenamento,
não medida de qualidade. Os contratos exigem campos presentes nas Silver de
negócio e tabelas Gold, embora campos físicos permitam NULL. As validações
Spark verificam presença, tipos, domínios e integridade; PK/FK não foram declaradas
como constraints do Unity Catalog. Não há garantia automática contra alterações
externas feitas sem executar o pipeline.

COUNT(*) mede linhas; SUM(qtde_vitimas) mede quantitativos publicados, não pessoas
distintas. Ausência não é automaticamente zero. S/N continua sem interpretação
oficial. Código municipal foi validado estruturalmente, sem certificação contra
cadastro externo. Dados não permitem inferir causalidade ou risco populacional.

Proveniência, licença CC BY 4.0, URLs e hashes: [validação das bases](validacao_bases_2025.md).
As evidências de execução são vinculadas aos snapshots, não uma confirmação
de que a publicação externa nunca foi revisada.

## Manutenção e escopo

Para atualizar esquema físico e inventários no zsh/WSL:

```zsh
python3 scripts/catalogar_databricks.py
```

O script lê os 12 objetos e o volume, grava a evidência e gera anexos. Falha se
o inventário de objetos divergir; mudanças semânticas exigem revisão manual
deste dicionário e da linhagem. Os domínios são extraídos da evidência de qualidade
identificada no script, não consultados novamente nas tabelas.

Item 18 cobre esta documentação, os anexos e a linhagem. Screenshots do catálogo
e dos resultados continuam no item 21; não são substituídos por estes arquivos.
