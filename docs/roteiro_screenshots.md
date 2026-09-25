# Capturas de evidências no Databricks

Status: item 21 pendente. A interface abriu autenticada, mas apresentou “Automated browser control detected” e informou que o console não suporta controle automatizado. Nenhuma captura de evidência foi produzida nesta tentativa. A autenticação e as execuções pelo CLI são independentes desse bloqueio da interface.

## Captura manual

Abra o workspace em seu navegador habitual. Use `Win + Shift + S` e salve as imagens em `evidencias/screenshots/`, na pasta do projeto. Inclua o nome do objeto ou job e o resultado legível. Se uma tela não comportar o conteúdo, use imagens adicionais; não altere os valores apresentados.

| Arquivo sugerido | Tela e conteúdo necessário |
| --- | --- |
| 01_catalogo.png | Catalog → workspace: schemas mvp_bronze, mvp_silver e mvp_gold. Expanda a Gold para mostrar as dimensões, fatos e view. |
| 02_bronze.png | Catalog → workspace → mvp_bronze → violencia_domestica_2025: nome completo, colunas e tipo Delta. Capture também feminicidio_2025 em imagem adicional. |
| 03_silver.png | Catalog → workspace → mvp_silver: tabelas de negócio e rejeições; abra uma tabela para mostrar tipos e campos de rastreabilidade. |
| 04_gold.png | Catalog → workspace → mvp_gold: fatos, dimensões e comparativo_municipio_mes; capture as colunas de uma fato. |
| 05_qualidade.png | Execução de qualidade abaixo: status Succeeded/SUCCESS e saída da tarefa com os controles. Use imagens adicionais para as duas fontes. |
| 06_reconciliacao.png | Execução Gold abaixo: status e saída com totais, dimensões e validação de chaves. |
| 07_analises.png | Execução analítica abaixo: status e saída com consultas/resultados. Expanda a saída da tarefa para mostrar os quantitativos. |

Links das execuções efetivamente registradas:

- [Qualidade — execução 183810729128831](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/1005669937621880/run/183810729128831)
- [Gold — execução 700142655207447](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/465875515640680/run/700142655207447)
- [Análises — execução 931355409551552](https://dbc-0a2b6ff1-9976.cloud.databricks.com/?o=7474657037018547#job/252723981011762/run/931355409551552)

## Valores para conferência

- Violência doméstica: 117.169 linhas; soma de qtde_vitimas = 162.032.
- Feminicídio: 381 linhas; soma = 391, sendo 213 tentados e 178 consumados.
- Dimensões: 365 dias, 853 municípios e 174 naturezas.
- Qualidade: zero erros estruturais e zero duplicidades; Silver com zero rejeições.
- Análises: sete consultas para quatro perguntas; dezembro soma 14.771 na fonte doméstica e 57 na fonte feminicídio.

Esses números servem para comparar com a tela, não para montar uma imagem substituta da interface. Os [gráficos exportados](resultados_analiticos.md) e as evidências JSON já existentes complementam as capturas. Não são screenshots do console. A linhagem documentada no projeto não deve ser apresentada como captura de linhagem automática do Unity Catalog.

Após salvar as imagens, conferir legibilidade, associar cada imagem ao objeto/execução correspondente e inserir os links no README. Só então marcar o item 21 como concluído.
