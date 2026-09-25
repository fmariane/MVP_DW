# Execução no Databricks Free Edition

## Ambiente confirmado

- CLI executada no WSL Ubuntu-20.04, perfil OAuth `MVP_DW`.
- Catálogo `workspace`; schemas `mvp_bronze`, `mvp_silver` e `mvp_gold`.
- CSVs originais no volume `/Volumes/workspace/mvp_bronze/arquivos`.
- Notebook remoto: `/Workspace/Users/f_mariane@hotmail.com/MVP_DW/01_bronze`.
- Código versionável: [01_bronze.py](../notebooks/01_bronze.py).
- Configuração do job: [bronze_job.json](../databricks/bronze_job.json).
- Job serverless criado: `699928499146328`. Sem agendamento.

## Executar pelo zsh no WSL

Os comandos pressupõem o diretório raiz deste repositório e a CLI autenticada.

```zsh
databricks auth profiles
databricks jobs run-now 699928499146328 --no-wait --profile MVP_DW --output json
```

Copie o `run_id` retornado e consulte:

```zsh
databricks jobs get-run ID_DA_EXECUCAO --profile MVP_DW --output json
```

O resultado contém `tasks[].run_id`. Use o ID da tarefa para obter o relatório:

```zsh
databricks jobs get-run-output ID_DA_TAREFA --profile MVP_DW --output json
```

Para enviar uma edição do notebook de código deste projeto:

```zsh
databricks workspace import /Workspace/Users/f_mariane@hotmail.com/MVP_DW/01_bronze \
  --file notebooks/01_bronze.py --format SOURCE --language PYTHON \
  --overwrite --profile MVP_DW
```

Use `jobs create --json @databricks/bronze_job.json --profile MVP_DW` apenas se precisar
criar outro job. Para o job existente, use `run-now`.

## Contrato da Bronze

1. Confere cabeçalho e SHA-256 dos dois arquivos contra as cópias inspecionadas.
2. Preserva cópias binárias em `arquivos/snapshots/<sha256>/<arquivo>.csv`.
3. Lê os CSVs com separador `;`, UTF-8 e todos os campos originais como texto.
4. Confere as linhas e somas de cada fonte antes da publicação.
5. Cria tabelas Delta `workspace.mvp_bronze.violencia_domestica_2025` e
   `workspace.mvp_bronze.feminicidio_2025`, adicionando `arquivo_origem`
   (caminho da cópia preservada), `arquivo_sha256` e `ingerido_em` em UTC.
6. Relê cada tabela, confere totais e metadados e compara os campos originais
   nos dois sentidos com `exceptAll`, preservando também multiplicidades.
7. Retorna relatório JSON no resultado do notebook.

A repetição valida o snapshot existente sem inserir ou sobrescrever linhas.
Um arquivo revisado, uma tabela com outro hash ou qualquer divergência bloqueia
a execução e exige análise. As duas tabelas são gravadas individualmente:
não há transação conjunta. Se uma falhar depois da outra, a reexecução valida
a existente e pode completar a ausente.

| Fonte | Linhas esperadas | Soma de qtde_vitimas |
| --- | ---: | ---: |
| Violência doméstica | 117169 | 162032 |
| Feminicídio | 381 | 391 |

As somas são quantitativos publicados, não pessoas distintas. S/N continua
preservado sem interpretação. Esta etapa não substitui o diagnóstico completo
de qualidade, a Silver, a Gold nem a reexecução integral do pipeline.

## Evidências

Resultados remotos e relatórios são guardados em [evidencias](../evidencias/).
Screenshots do catálogo e dos resultados ainda devem ser capturados para a entrega.

- [Carga aprovada](../evidencias/bronze_207087315322185.json): ambas as tabelas criadas e validadas.
- [Reexecução aprovada](../evidencias/bronze_1001589874049096.json): mesmos IDs Delta, linhas e somas; ambos os snapshots existentes validados sem nova inserção.
- A primeira tentativa (`195278572575128`) falhou antes da criação das tabelas porque o Spark Connect deste runtime não aceitou o alias `errorifexists`. O notebook foi corrigido para `error`; as duas execuções acima usam a versão corrigida.

Para guardar a evidência de uma execução concluída com sucesso:

```zsh
python3 scripts/capturar_evidencia_bronze.py ID_DA_EXECUCAO
```

O script salva o estado remoto e o relatório do notebook, sem copiar credenciais.

## Diagnóstico de qualidade

Notebook `02_qualidade`, job serverless `1005669937621880`, sem agendamento.
O diagnóstico lê versões Delta fixadas no início da análise e não altera as
tabelas. Testes sintéticos são executados antes dos controles das fontes.

```zsh
databricks jobs run-now 1005669937621880 --no-wait --profile MVP_DW --output json
databricks jobs get-run ID_DA_EXECUCAO --profile MVP_DW --output json
python3 scripts/capturar_evidencia_bronze.py ID_DA_EXECUCAO --etapa qualidade
```

O nome histórico do coletor foi mantido, mas a opção `--etapa qualidade` salva
o diagnóstico em `evidencias/qualidade_<run_id>.json`. `status=CONCLUIDO` significa
que a análise terminou; consulte também `bloqueios_estruturais` e as ressalvas
para decidir a continuidade. Não confundir sucesso do job com aprovação dos dados.

Execução comprovada: [relatório](qualidade_bronze.md). Contrato para a próxima
etapa: [regras Silver](regras_silver.md).

## Executar a Silver

Notebook `03_silver`, job serverless `1075813885223029`, sem agendamento.
Código em [03_silver.py](../notebooks/03_silver.py) e configuração em
[silver_job.json](../databricks/silver_job.json).

```zsh
databricks jobs run-now 1075813885223029 --no-wait --profile MVP_DW --output json
databricks jobs get-run ID_DA_EXECUCAO --profile MVP_DW --output json
python3 scripts/capturar_evidencia_bronze.py ID_DA_EXECUCAO --etapa silver
```

O notebook testa os tratamentos, lê versões Delta fixas da Bronze, prepara
candidatos e registra rejeições antes de publicar. Cada tabela de rejeições
possui `execucao_id`; uma execução sem rejeições mantém essas tabelas vazias.
Falhas de qualidade bloqueiam a publicação, sem apagar uma versão anterior.

Uma Silver já existente é comparada com o candidato em todos os campos, exceto
o timestamp técnico `tratado_em`. Se houver diferença, o job falha; não há
sobrescrita automática. Se corresponder, a tabela é preservada sem novas linhas.
As duas tabelas não formam uma transação única; se houver falha de infraestrutura
entre as gravações, a reexecução valida a existente e cria a ausente.

## Executar a Gold

Notebook `04_gold`, job serverless `465875515640680`, sem agendamento.
Código em [04_gold.py](../notebooks/04_gold.py) e configuração em
[gold_job.json](../databricks/gold_job.json).

```zsh
databricks jobs run-now 465875515640680 --no-wait --profile MVP_DW --output json
databricks jobs get-run ID_DA_EXECUCAO --profile MVP_DW --output json
python3 scripts/capturar_evidencia_bronze.py ID_DA_EXECUCAO --etapa gold
```

A Gold lê versões Delta fixas das Silver, gera três dimensões e duas fatos e
valida chaves, campos obrigatórios e totais. Cada junção exige uma dimensão
única pela chave, nenhuma FK órfã e preservação de linhas e soma. Os controles
são repetidos após a gravação. PK/FK são garantidas pelos controles da execução,
não por constraints declaradas no catálogo.

A view `workspace.mvp_gold.comparativo_municipio_mes` agrega cada fonte antes
do FULL OUTER JOIN. Mantém medidas separadas, indicadores de presença e nulos
nas ausências. Não representa total combinado ou taxa de conversão entre fontes.

Todas as tabelas existentes devem corresponder aos candidatos antes de qualquer
nova gravação. O job cria objetos ausentes; não sobrescreve tabelas divergentes.
Não há transação conjunta entre as cinco tabelas e a view. Falhas intermediárias
exigem reexecução e estado final aprovado antes do consumo analítico.

## Atualizar o catálogo e a linhagem

```zsh
python3 scripts/catalogar_databricks.py
```

Consulta somente metadados do Unity Catalog pela CLI. Grava
`evidencias/catalogo_databricks.json`, gera `docs/esquema_fisico.md` e
`docs/dominios_observados.md`. O último usa os inventários da evidência de qualidade
já aprovada, sem executar novamente consultas de perfil dos dados.
Descrições e transformações são mantidas em [catalogo_dados.md](catalogo_dados.md)
e [linhagem_dados.md](linhagem_dados.md). A extração confirmou 12 objetos,
136 colunas de primeiro nível e um volume. Não modifica as tabelas remotas.

## Consultas e gráficos

Notebook `05_analises`, job `252723981011762`, sem agendamento. Sete consultas
cobrem as quatro perguntas originais, com versões Gold fixadas, percentuais
por fonte/grupo e reconciliação dos totais. Resultados são exibidos no notebook
e retornados em JSON; nenhuma nova tabela de negócio é criada.

```zsh
databricks jobs run-now 252723981011762 --no-wait --profile MVP_DW --output json
databricks jobs get-run ID_DA_EXECUCAO --profile MVP_DW --output json
python3 scripts/capturar_evidencia_bronze.py ID_DA_EXECUCAO --etapa analises
```

Renderização local, com Python 3.12 disponível e as dependências instaladas:

```zsh
python3.12 -m pip install -r requirements-graficos.txt
python3.12 scripts/gerar_graficos.py evidencias/analises_ID_DA_EXECUCAO.json
```

O builder gera sete PNG, sete SVG, sete resultados JSON completos, SQL reproduzível
e relatório interpretativo. A extração pela CLI funciona no Python 3.8 do WSL;
a renderização foi validada no Python 3.12 local. [Resultado aprovado](resultados_analiticos.md).
