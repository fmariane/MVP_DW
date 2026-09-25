# Contexto de Negócios e Perguntas

## Contexto

O planejamento de ações de enfrentamento à violência contra a mulher requer informações organizadas sobre a distribuição territorial e temporal dos registros. Este MVP reúne duas bases publicadas pela Polícia Civil de Minas Gerais: violência doméstica e familiar contra a mulher e vítimas de feminicídio, ambas referentes a 2025.

O problema abordado é transformar esses arquivos em uma base analítica rastreável, com métricas consistentes e documentação das diferenças entre as fontes. O público de referência são analistas interessados em subsidiar estudos e discussões sobre prioridades de investigação. Os resultados descreverão os registros publicados, sem estimar a totalidade da violência ocorrida no estado.

## Objetivo

Construir um pipeline reprodutível no Databricks para ingerir, validar, padronizar e modelar as duas bases de 2025, permitindo analisar a distribuição dos quantitativos de vítimas registrados por período, município, região e classificação disponível em cada fonte.

O fluxo preservará os arquivos originais na Bronze, aplicará tratamentos documentados na Silver e disponibilizará duas tabelas fato com dimensões compartilhadas na Gold. A entrega incluirá código, catálogo, verificações de qualidade, análises e evidências de persistência e execução na nuvem.

## Escopo

- Minas Gerais; datas dos fatos de 01/01/2025 a 31/12/2025.
- Arquivos locais `feminicidio_2025.csv` e `violencia_domestica_2025.csv`.
- Origem: [Portal de Dados Abertos de MG — PCMG](https://dados.mg.gov.br/pt_PT/dataset/violencia-contra-mulher).
- Licença dos dados: CC BY 4.0, conforme `datapackage.json`; atribuir a fonte.
- Base SES/Sinan, população, previsão e análises causais ficam fora do escopo inicial.
- Prazo de entrega definido pelo usuário: 25/09/2026.

## Perguntas de negócio

1. **Como os quantitativos de vítimas registrados se distribuem pelos meses de 2025 em cada base?** Somar `qtde_vitimas` por mês, mantendo as duas fontes separadas, e discutir variações mensais. Um ano permite descrição intra-anual, não comprovação de sazonalidade recorrente.
2. **Quais municípios e regiões de segurança concentram os maiores quantitativos em cada base?** Apresentar somas e participação no total da própria fonte. Os rankings indicam volume registrado, não risco por habitante.
3. **Quais naturezas de delito concentram os maiores quantitativos na base de violência doméstica?** Agregar por `natureza_delito`, sem converter os códigos S/N. Interpretar os valores como quantitativos publicados por natureza, sem afirmar pessoas únicas.
4. **Como os quantitativos de vítimas de feminicídio tentado e consumado se distribuem por região e mês?** Utilizar exclusivamente os rótulos explícitos TENTADO e CONSUMADO da base de feminicídios, apresentando totais e composição dentro dessa base.

## Métricas e regras de interpretação

A medida principal será `SUM(qtde_vitimas)` por fonte e grupo. A participação percentual será a soma do grupo dividida pelo total da mesma fonte e do mesmo recorte, com denominador explícito. Contagens de linhas serão indicadores técnicos de controle da carga, não contagens de crimes.

Não somar as duas fontes em um total geral: a sobreposição de registros não pode ser determinada com os campos publicados. Não calcular uma taxa de evolução de violência doméstica para feminicídio. Não vincular pessoas ou ocorrências por município e data.

Quando for necessário comparar indicadores lado a lado, agregar cada fato separadamente por município e mês antes da junção. Ausência de linha não será automaticamente convertida em zero sem validar cobertura e semântica da publicação.

Os códigos S/N de `tentado_consumado` na base de violência doméstica permanecerão preservados como códigos de significado pendente. Não são necessários para responder às quatro perguntas. A validação semântica e as limitações estão em [Validação das bases](validacao_bases_2025.md).

## Critérios de sucesso

Executar o pipeline de ponta a ponta na nuvem, reconciliar os totais com os arquivos originais, documentar campos e transformações e responder às perguntas com consultas, interpretação e screenshots. Preservar as perguntas originais e explicar na autoavaliação qualquer objetivo não alcançado. Nenhuma execução na nuvem é afirmada nesta etapa de planejamento.
