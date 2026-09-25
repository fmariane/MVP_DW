# Databricks notebook source
# MAGIC %md
# MAGIC # Gold — duas estrelas PCMG 2025
# MAGIC Dimensões compartilhadas; fatos separadas. Chaves e totais são verificados
# MAGIC antes/depois das junções e novamente nas tabelas persistidas.

# COMMAND ----------
import hashlib
import json
from datetime import datetime, timezone
from functools import reduce
from pyspark.sql import functions as F

spark.conf.set("spark.sql.session.timeZone", "UTC")
SCHEMA = "workspace.mvp_gold"
META = ["arquivo_origem", "arquivo_sha256", "ingerido_em"]
SOURCES = [
    dict(name="violencia_domestica_2025", fact="fato_violencia_domestica", rows=117169, victims=162032,
         sha256="0d6e677ab65e7d04834904080ec0296eccf8dabd6013fe45910c9d754f94b4fe", category="codigo_tentado_consumado", domain=["S", "N"]),
    dict(name="feminicidio_2025", fact="fato_feminicidio", rows=381, victims=391,
         sha256="364dec0197c1d9c40a050883573ce22efd280a43114680fc1491e40db6e89630", category="situacao", domain=["TENTADO", "CONSUMADO"]),
]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def complete(df):
    bad = [F.col(c).isNull() for c in df.columns]
    bad += [F.trim(F.col(c)) == "" for c, dtype in df.dtypes if dtype == "string"]
    require(df.filter(reduce(lambda a, b: a | b, bad)).limit(1).count() == 0, "Campo obrigatório ausente")

def unique(df, keys):
    complete(df.select(*keys))
    require(df.groupBy(*keys).count().filter(F.col("count") > 1).limit(1).count() == 0,
            f"Chave duplicada: {keys}")

def metrics(df):
    return df.agg(F.count("*").alias("linhas"), F.sum("qtde_vitimas").alias("soma_vitimas")).first().asDict()

def same(left, right):
    cols = left.columns
    require(cols == right.columns, "Colunas divergentes")
    require(left.exceptAll(right.select(*cols)).limit(1).count() == 0 and
            right.select(*cols).exceptAll(left).limit(1).count() == 0, "Conteúdo divergente")

def checked_join(fact, dim, keys, label):
    unique(dim, keys)
    require(fact.join(dim.select(*keys), keys, "left_anti").limit(1).count() == 0, f"FK sem correspondência: {label}")
    before = metrics(fact)
    joined = fact.join(dim, keys, "inner")
    after = metrics(joined)
    require(before == after, f"Junção alterou linhas ou medidas: {label}")
    return joined, dict(juncao=label, antes=before, depois=after, chaves_orfas=0)

def compare_stored(stored, expected):
    require([(f.name, f.dataType.simpleString()) for f in stored.schema] ==
            [(f.name, f.dataType.simpleString()) for f in expected.schema], "Tipos persistidos divergentes")
    same(stored, expected)

# COMMAND ----------
# Testes: guardas contra chaves duplicadas, FK órfã e multiplicação em junções.
test_fact = spark.createDataFrame([(1, 2), (2, 3)], "chave int, qtde_vitimas long")
test_dim = spark.createDataFrame([(1,), (2,)], "chave int")
_, test_ok = checked_join(test_fact, test_dim, ["chave"], "teste_valido")
require(test_ok["depois"] == dict(linhas=2, soma_vitimas=5), "Teste de preservação falhou")
for dim, expected_error in [(spark.createDataFrame([(1,), (1,), (2,)], "chave int"), "Chave duplicada"),
                            (spark.createDataFrame([(1,)], "chave int"), "FK sem correspondência")]:
    try:
        checked_join(test_fact, dim, ["chave"], "teste_invalido")
    except ValueError as error:
        require(expected_error in str(error), "Falha inesperada no teste")
    else:
        raise ValueError("Uma junção inválida foi aceita")
test_name = "AMEAÇA"
test_hash = spark.range(1).select(F.sha2(F.encode(F.lit(test_name), "UTF-8"), 256)).first()[0]
require(test_hash == hashlib.sha256(test_name.encode("utf-8")).hexdigest(), "SHA-256 UTF-8 divergente")

# COMMAND ----------
silver = {}
lineage = []
for source in SOURCES:
    table = f"workspace.mvp_silver.{source['name']}"
    version = int(spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()["version"])
    df = spark.sql(f"SELECT * FROM {table} VERSION AS OF {version}")
    require(metrics(df) == dict(linhas=source["rows"], soma_vitimas=source["victims"]), "Baseline Silver divergente")
    require(df.filter(~F.coalesce((F.col("arquivo_sha256") == source["sha256"]) &
                    (F.col("versao_regras") == "silver_v1"), F.lit(False))).limit(1).count() == 0, "Snapshot Silver inesperado")
    silver[source["name"]] = df
    lineage.append(dict(tabela=table, versao_delta=version, arquivo_sha256=source["sha256"]))

dates = spark.sql("SELECT explode(sequence(DATE '2025-01-01', DATE '2025-12-31', INTERVAL 1 DAY)) AS data")
tempo = dates.select(F.date_format("data", "yyyyMMdd").cast("int").alias("data_key"), "data",
                     F.year("data").alias("ano"), F.month("data").alias("mes"),
                     F.dayofmonth("data").alias("dia"), F.quarter("data").alias("trimestre"))
geo_cols = ["municipio_cod", "municipio_fato", "risp", "rmbh"]
geo = reduce(lambda a, b: a.unionByName(b), [df.select(*geo_cols) for df in silver.values()]).distinct()
unique(geo, ["municipio_cod"])
municipio = geo.select("municipio_cod", F.col("municipio_fato").alias("municipio_nome"), F.lit("MG").alias("uf"),
                       F.col("risp").alias("risp_cod"), F.col("rmbh").alias("recorte_metropolitano"))
natureza = silver[SOURCES[0]["name"]].select(F.upper(F.trim("natureza_delito")).alias("natureza_nome")).distinct()
natureza = natureza.select(F.sha2(F.encode("natureza_nome", "UTF-8"), 256).alias("natureza_key"), "natureza_nome")
dims = {"dim_tempo": tempo, "dim_municipio": municipio, "dim_natureza_delito": natureza}
dim_specs = {"dim_tempo": (["data_key"], 365), "dim_municipio": (["municipio_cod"], 853), "dim_natureza_delito": (["natureza_key"], 174)}
for name, df in dims.items():
    complete(df)
    keys, count = dim_specs[name]
    unique(df, keys)
    require(df.count() == count, f"Cardinalidade inesperada: {name}")
unique(tempo, ["data"])
unique(natureza, ["natureza_nome"])

# COMMAND ----------
facts = {}
join_reports = {}
for source in SOURCES:
    base = silver[source["name"]]
    joined, time_check = checked_join(base, tempo.select(F.col("data").alias("data_fato"), "data_key"), ["data_fato"], "tempo")
    joined, geo_check = checked_join(joined, municipio.select("municipio_cod"), ["municipio_cod"], "municipio")
    checks = [time_check, geo_check]
    cols = ["data_key", "municipio_cod"]
    if source["fact"] == "fato_violencia_domestica":
        joined, nature_check = checked_join(joined, natureza.select(F.col("natureza_nome").alias("natureza_delito"), "natureza_key"), ["natureza_delito"], "natureza")
        checks.append(nature_check)
        cols.append("natureza_key")
    fact = joined.select(*cols, F.col("tentado_consumado").alias(source["category"]), "qtde_vitimas", *META)
    complete(fact)
    unique(fact, cols + [source["category"]])
    require(fact.filter(~F.col(source["category"]).isin(source["domain"]) | (F.col("qtde_vitimas") <= 0)).limit(1).count() == 0, "Domínio inválido na fato")
    facts[source["fact"]] = fact
    join_reports[source["fact"]] = checks

def comparison(facts, tempo):
    aggregates = []
    for source, measure in zip(SOURCES, ["vitimas_violencia_domestica", "vitimas_feminicidio"]):
        fact = facts[source["fact"]].join(tempo.select("data_key", "ano", "mes"), "data_key", "inner")
        aggregates.append(fact.groupBy("municipio_cod", "ano", "mes").agg(F.sum("qtde_vitimas").alias(measure))
                          .withColumn("presente_" + measure, F.lit(True)))
    keys = ["municipio_cod", "ano", "mes"]
    for agg in aggregates:
        unique(agg, keys)
    combined = aggregates[0].join(aggregates[1], keys, "full_outer")
    for measure in ["vitimas_violencia_domestica", "vitimas_feminicidio"]:
        combined = combined.withColumn("presente_" + measure, F.coalesce(F.col("presente_" + measure), F.lit(False)))
    unique(combined, keys)
    for agg, measure in zip(aggregates, ["vitimas_violencia_domestica", "vitimas_feminicidio"]):
        same(agg, combined.filter(F.col("presente_" + measure)).select(*agg.columns))
    return combined

# Testar também a comparação com presença/ausência em cada fonte.
test_time = spark.createDataFrame([(20250101, 2025, 1)], "data_key int, ano int, mes int")
test_facts = {SOURCES[0]["fact"]: spark.createDataFrame([("A", 20250101, 2), ("B", 20250101, 3)], "municipio_cod string, data_key int, qtde_vitimas long"),
              SOURCES[1]["fact"]: spark.createDataFrame([("A", 20250101, 1), ("C", 20250101, 4)], "municipio_cod string, data_key int, qtde_vitimas long")}
test_comp = comparison(test_facts, test_time)
require(test_comp.count() == 3 and test_comp.filter(F.col("municipio_cod") == "B").first().vitimas_feminicidio is None,
        "Comparação deve manter municípios exclusivos e ausência como NULL")
comparative = comparison(facts, tempo)

# COMMAND ----------
# Verificar todos os candidatos e todas as tabelas existentes antes de publicar.
candidates = {**dims, **facts}
for name, expected in candidates.items():
    table = f"{SCHEMA}.{name}"
    if spark.catalog.tableExists(table):
        compare_stored(spark.table(table), expected)

reports = []
for name, expected in candidates.items():
    table = f"{SCHEMA}.{name}"
    if spark.catalog.tableExists(table):
        action = "snapshot_existente_validado"
    else:
        expected.write.format("delta").mode("error").saveAsTable(table)
        action = "criada"
    stored = spark.table(table)
    compare_stored(stored, expected)
    complete(stored)
    detail = spark.sql(f"DESCRIBE DETAIL {table}").select("format", "id").first().asDict()
    require(detail["format"] == "delta", "Formato inesperado")
    record = dict(tabela=table, acao=action, linhas=stored.count(), delta_id=detail["id"], formato=detail["format"],
                  tipos={f.name: f.dataType.simpleString() for f in stored.schema})
    if name in facts:
        record.update(metrics(stored))
        record["juncoes"] = join_reports[name]
    reports.append(record)

# Verificar FKs e medidas usando apenas as tabelas publicadas.
persisted_checks = []
for source in SOURCES:
    fact = spark.table(f"{SCHEMA}.{source['fact']}")
    for dim_name, keys in [("dim_tempo", ["data_key"]), ("dim_municipio", ["municipio_cod"])] + (
            [("dim_natureza_delito", ["natureza_key"])] if source["fact"] == "fato_violencia_domestica" else []):
        fact, check = checked_join(fact, spark.table(f"{SCHEMA}.{dim_name}").select(*keys), keys, dim_name)
        persisted_checks.append(dict(fato=source["fact"], **check))
    require(metrics(fact) == dict(linhas=source["rows"], soma_vitimas=source["victims"]), "Totais persistidos divergentes")

# Uma view comparativa agrega cada fato ANTES de combinar indicadores.
view = f"{SCHEMA}.comparativo_municipio_mes"
spark.sql(f"""CREATE VIEW IF NOT EXISTS {view} AS
WITH d AS (
  SELECT f.municipio_cod, t.ano, t.mes, SUM(f.qtde_vitimas) AS vitimas_violencia_domestica
  FROM {SCHEMA}.fato_violencia_domestica f JOIN {SCHEMA}.dim_tempo t USING(data_key)
  GROUP BY f.municipio_cod, t.ano, t.mes
), f AS (
  SELECT f.municipio_cod, t.ano, t.mes, SUM(f.qtde_vitimas) AS vitimas_feminicidio
  FROM {SCHEMA}.fato_feminicidio f JOIN {SCHEMA}.dim_tempo t USING(data_key)
  GROUP BY f.municipio_cod, t.ano, t.mes
)
SELECT COALESCE(d.municipio_cod,f.municipio_cod) AS municipio_cod,
       COALESCE(d.ano,f.ano) AS ano, COALESCE(d.mes,f.mes) AS mes,
       d.vitimas_violencia_domestica, d.municipio_cod IS NOT NULL AS presente_vitimas_violencia_domestica,
       f.vitimas_feminicidio, f.municipio_cod IS NOT NULL AS presente_vitimas_feminicidio
FROM d FULL OUTER JOIN f ON d.municipio_cod=f.municipio_cod AND d.ano=f.ano AND d.mes=f.mes
""")
same(comparative, spark.table(view).select(*comparative.columns))
view_report = dict(view=view, linhas=spark.table(view).count(), medidas_separadas=True, ausencia_permanece_nula=True)
result = dict(etapa="gold", status="APROVADO", executado_em_utc=datetime.now(timezone.utc).isoformat(),
              testes_sinteticos="APROVADOS", fontes_silver=lineage, tabelas=reports,
              validacoes_persistidas=persisted_checks, comparativo=view_report,
              ressalvas=["S/N não traduzido.", "Sem contagem de pessoas únicas nem soma entre fontes.",
                         "Integridade verificada pelo pipeline; PK/FK não declaradas como constraints no catálogo."])
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))
