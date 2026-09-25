# Catálogo — camada Gold

Tabelas implantadas em `workspace.mvp_gold` e verificadas no pipeline: [evidência](validacao_gold.md). Todos os campos das cinco tabelas abaixo são obrigatórios. PK/FK são chaves lógicas validadas pelo notebook, não constraints declaradas no catálogo.

## dim_tempo

Uma linha por dia, gerada pelo calendário completo de 2025.

| Campo | Tipo lógico | Descrição e domínio | Origem |
| --- | --- | --- | --- |
| data_key | INT | PK determinística AAAAMMDD | Calendário derivado |
| data | DATE | Dia entre 2025-01-01 e 2025-12-31; único | Calendário |
| ano | INT | 2025 | Ano de data |
| mes | INT | 1 a 12 | Mês de data |
| dia | INT | 1 a 31, válido para mês/ano | Dia de data |
| trimestre | INT | 1 a 4 | Trimestre de data |

## dim_municipio

Uma linha por código publicado; atributos conciliados entre ambas as fontes.

| Campo | Tipo lógico | Descrição e domínio | Origem |
| --- | --- | --- | --- |
| municipio_cod | STRING | PK; seis dígitos nas fontes atuais, preservados como texto | municipio_cod das duas Silver |
| municipio_nome | STRING | Nome padronizado não vazio; regra explícita para 315990 | municipio_fato; trim e correspondência documentada |
| uf | STRING | Constante MG, escopo da publicação | Metadados do conjunto |
| risp_cod | STRING | Código regional textual; valores 1 a 19 no snapshot | risp das fontes, sem inventar descrição regional |
| recorte_metropolitano | STRING | Belo Horizonte; RMBH (Sem BH); Interior de MG | rmbh das fontes; não é booleano |

## dim_natureza_delito

Uma linha por natureza da base de violência doméstica; 174 valores observados.

| Campo | Tipo lógico | Descrição e domínio | Origem |
| --- | --- | --- | --- |
| natureza_key | STRING | PK; SHA-256 hexadecimal de 64 caracteres | SHA-256 do nome normalizado em UTF-8 |
| natureza_nome | STRING | Categoria não vazia; valores distintos publicados, sem reclassificação | upper(trim(natureza_delito)) da Silver doméstica |

O domínio completo é o conteúdo da dimensão gerada a partir da fonte. Novas categorias exigem registro e validação; não se impõe uma lista inventada de delitos.

## fato_violencia_domestica

Chave composta: data_key + municipio_cod + natureza_key + codigo_tentado_consumado. Uma linha por grupo observado, não por pessoa ou ocorrência identificável.

| Campo | Tipo lógico | Descrição e domínio | Origem |
| --- | --- | --- | --- |
| data_key | INT | FK dim_tempo | data_fato validada, codificada AAAAMMDD |
| municipio_cod | STRING | FK dim_municipio | Código original preservado |
| natureza_key | STRING | FK dim_natureza_delito | Lookup do nome normalizado |
| codigo_tentado_consumado | STRING | S ou N; significado pendente, não traduzir | tentado_consumado original |
| qtde_vitimas | BIGINT | Quantitativo publicado; inteiro positivo; 1 a 31 observado, não teto permanente | Conversão de qtde_vitimas sem agregação adicional |
| arquivo_origem | STRING | Caminho da cópia CSV preservada por hash no volume | Metadado Bronze, propagado pela Silver |
| arquivo_sha256 | STRING | Hash hexadecimal de 64 caracteres do arquivo original | Bytes do arquivo, calculado na ingestão |
| ingerido_em | TIMESTAMP | Instante UTC da ingestão; não é data do fato | Metadado Bronze, propagado sem substituir pela data de transformação |

## fato_feminicidio

Chave composta: data_key + municipio_cod + situacao. Uma linha por grupo observado de município, dia e situação.

| Campo | Tipo lógico | Descrição e domínio | Origem |
| --- | --- | --- | --- |
| data_key | INT | FK dim_tempo | data_fato validada, codificada AAAAMMDD |
| municipio_cod | STRING | FK dim_municipio | Código original preservado |
| situacao | STRING | TENTADO ou CONSUMADO | tentado_consumado da fonte de feminicídio |
| qtde_vitimas | BIGINT | Quantitativo publicado; inteiro positivo; 1 a 2 observado, não teto permanente | Conversão de qtde_vitimas sem agregação adicional |
| arquivo_origem | STRING | Caminho da cópia CSV preservada por hash no volume | Metadado Bronze, propagado pela Silver |
| arquivo_sha256 | STRING | Hash hexadecimal de 64 caracteres | Bytes do arquivo original |
| ingerido_em | TIMESTAMP | Instante UTC da ingestão | Metadado Bronze, propagado pela Silver |

## Escopo do catálogo

Tipos conferidos nas tabelas persistidas e no [esquema físico](esquema_fisico.md). Este dicionário integra o [catálogo completo](catalogo_dados.md), que inclui Bronze, Silver, rejeições e [linhagem](linhagem_dados.md). Screenshots permanecem pendentes. A origem primária e os hashes estão em [validacao_bases_2025.md](validacao_bases_2025.md); decisões e medidas em [modelagem_dimensional.md](modelagem_dimensional.md).

## View comparativo_municipio_mes

Nome completo: `workspace.mvp_gold.comparativo_municipio_mes`. Chave lógica:
municipio_cod + ano + mes; 9296 combinações observadas no snapshot.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| municipio_cod | STRING | Município presente em pelo menos uma fonte no mês |
| ano | INT | Ano derivado da dim_tempo |
| mes | INT | Mês derivado da dim_tempo |
| vitimas_violencia_domestica | BIGINT, anulável | Soma independente da fato doméstica; NULL quando ausente |
| presente_vitimas_violencia_domestica | BOOLEAN | Indica existência de registros domésticos na chave |
| vitimas_feminicidio | BIGINT, anulável | Soma independente da fato feminicídio; NULL quando ausente |
| presente_vitimas_feminicidio | BOOLEAN | Indica existência de registros de feminicídio na chave |

Linhagem: cada fato → dim_tempo → agregação por município/ano/mês → FULL OUTER JOIN.
As duas medidas não devem ser somadas nem interpretadas como trajetória de pessoas.
