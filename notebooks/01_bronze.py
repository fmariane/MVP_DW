# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze — PCMG, Minas Gerais, 2025
# MAGIC Preserva os campos publicados como texto e os arquivos por SHA-256.
# MAGIC Uma repetição valida o snapshot existente sem acrescentar linhas.
# MAGIC As somas representam quantitativos publicados, não pessoas únicas.

# COMMAND ----------
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

spark.conf.set("spark.sql.session.timeZone", "UTC")
BASE = Path("/Volumes/workspace/mvp_bronze/arquivos")
SCHEMA = "workspace.mvp_bronze"
COMMON = ["municipio_cod", "municipio_fato", "data_fato", "mes", "ano", "risp", "rmbh"]
SOURCES = [
    dict(name="violencia_domestica_2025", rows=117169, victims=162032,
         sha256="0d6e677ab65e7d04834904080ec0296eccf8dabd6013fe45910c9d754f94b4fe",
         columns=COMMON + ["natureza_delito", "tentado_consumado", "qtde_vitimas"]),
    dict(name="feminicidio_2025", rows=381, victims=391,
         sha256="364dec0197c1d9c40a050883573ce22efd280a43114680fc1491e40db6e89630",
         columns=COMMON + ["tentado_consumado", "qtde_vitimas"]),
]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def metrics(df):
    return df.selectExpr("*", "try_cast(qtde_vitimas AS BIGINT) AS _q").agg(
        F.count("*").alias("linhas"),
        F.sum("_q").alias("soma_vitimas"),
        F.sum(F.when(F.col("_q").isNull(), 1).otherwise(0)).alias("quantidades_invalidas"),
    ).first().asDict()

def validate_totals(df, source):
    result = metrics(df)
    require(result == dict(linhas=source["rows"], soma_vitimas=source["victims"],
                           quantidades_invalidas=0), f"Totais divergentes: {source['name']}: {result}")
    return result

def validate_table(df, raw, source, archive):
    validate_totals(df, source)
    require(df.columns == source["columns"] + ["arquivo_origem", "arquivo_sha256", "ingerido_em"],
            "Colunas Bronze inesperadas")
    require(all(isinstance(df.schema[c].dataType, StringType) for c in source["columns"]),
            "Os campos originais devem permanecer texto")
    require(df.filter(F.col("arquivo_sha256").isNull() |
                      (F.col("arquivo_sha256") != source["sha256"]) |
                      F.col("arquivo_origem").isNull() |
                      (F.col("arquivo_origem") != str(archive)) |
                      F.col("ingerido_em").isNull()).limit(1).count() == 0,
            "Metadados ausentes ou snapshot diferente; não sobrescrever")
    stored = df.select(*source["columns"])
    require(raw.exceptAll(stored).limit(1).count() == 0 and
            stored.exceptAll(raw).limit(1).count() == 0,
            "Conteúdo persistido diferente da fonte (incluindo multiplicidades)")

# COMMAND ----------
# Validar ambas as fontes antes de publicar qualquer tabela.
prepared = []
for source in SOURCES:
    original = BASE / f"{source['name']}.csv"
    content = original.read_bytes()
    require(hashlib.sha256(content).hexdigest() == source["sha256"],
            f"Hash divergente: {original}; revisão da fonte requer análise")
    header = content.decode("utf-8-sig").splitlines()[0].split(";")
    require(header == source["columns"], f"Cabeçalho inesperado: {original}")
    archive = BASE / "snapshots" / source["sha256"] / original.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        with archive.open("xb") as target:
            target.write(content)
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == source["sha256"],
            f"Cópia arquivada divergente: {archive}")
    raw = (spark.read.schema(StructType([StructField(c, StringType(), True) for c in source["columns"]]))
           .option("header", True).option("sep", ";").option("encoding", "UTF-8")
           .option("mode", "FAILFAST").option("enforceSchema", False)
           .option("ignoreLeadingWhiteSpace", False).option("ignoreTrailingWhiteSpace", False)
           .csv(str(archive)))
    validate_totals(raw, source)
    prepared.append((source, raw, archive))

# COMMAND ----------
results = []
for source, raw, archive in prepared:
    table = f"{SCHEMA}.{source['name']}"
    if spark.catalog.tableExists(table):
        action = "snapshot_existente_validado"
    else:
        candidate = (raw.withColumn("arquivo_origem", F.lit(str(archive)))
                     .withColumn("arquivo_sha256", F.lit(source["sha256"]))
                     .withColumn("ingerido_em", F.current_timestamp()))
        candidate.write.format("delta").mode("error").saveAsTable(table)
        action = "criada"
    persisted = spark.table(table)
    validate_table(persisted, raw, source, archive)
    detail = spark.sql(f"DESCRIBE DETAIL {table}").select("format", "id").first().asDict()
    require(detail["format"] == "delta", "A tabela deve ser Delta")
    results.append(dict(tabela=table, acao=action, arquivo_original=str(BASE / f"{source['name']}.csv"),
                        arquivo_snapshot=str(archive), arquivo_sha256=source["sha256"],
                        **metrics(persisted), formato=detail["format"], delta_id=detail["id"],
                        conteudo_original_preservado=True))
    display(persisted.limit(10))

# COMMAND ----------
report = dict(etapa="bronze", executado_em_utc=datetime.now(timezone.utc).isoformat(),
              status="APROVADO", fontes=results,
              observacao="COUNT mede linhas; SUM mede quantitativos publicados. Fontes não somadas.")
display(spark.createDataFrame(results))
dbutils.notebook.exit(json.dumps(report, ensure_ascii=False))
