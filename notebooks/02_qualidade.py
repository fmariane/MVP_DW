# Databricks notebook source
# MAGIC %md
# MAGIC # Qualidade da Bronze — PCMG 2025
# MAGIC Diagnóstico sem alterar tabelas. As leituras usam versões Delta registradas.
# MAGIC Regras verificam estrutura, não completude do registro de violência na sociedade.

# COMMAND ----------
import json
from datetime import datetime, timezone
from functools import reduce
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

spark.conf.set("spark.sql.session.timeZone", "UTC")
COMMON = ["municipio_cod", "municipio_fato", "data_fato", "mes", "ano", "risp", "rmbh"]
SOURCES = [
    dict(name="violencia_domestica_2025", rows=117169, victims=162032,
         sha256="0d6e677ab65e7d04834904080ec0296eccf8dabd6013fe45910c9d754f94b4fe",
         columns=COMMON + ["natureza_delito", "tentado_consumado", "qtde_vitimas"],
         domain=["S", "N"]),
    dict(name="feminicidio_2025", rows=381, victims=391,
         sha256="364dec0197c1d9c40a050883573ce22efd280a43114680fc1491e40db6e89630",
         columns=COMMON + ["tentado_consumado", "qtde_vitimas"],
         domain=["TENTADO", "CONSUMADO"]),
]
RMBH = ["Interior de MG", "Belo Horizonte", "RMBH (Sem BH)"]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def present(column):
    return F.col(column).isNotNull() & (F.trim(F.col(column)) != "")

def flagged(expression):
    # NULL lógico é falha, não aprovação silenciosa.
    return ~F.coalesce(expression, F.lit(False))

def prepared(df):
    return (df.withColumn("_data", F.expr("try_cast(trim(data_fato) AS DATE)"))
            .withColumn("_mes", F.expr("try_cast(trim(mes) AS INT)"))
            .withColumn("_ano", F.expr("try_cast(trim(ano) AS INT)"))
            .withColumn("_risp", F.expr("try_cast(trim(risp) AS INT)"))
            .withColumn("_q", F.expr("try_cast(trim(qtde_vitimas) AS BIGINT)")))

def rules(df, source):
    checks = {f"ausente__{c}": ~present(c) for c in source["columns"]}
    checks.update({
        "data_invalida": flagged(F.trim(F.col("data_fato")).rlike(r"^\d{4}-\d{2}-\d{2}$") & F.col("_data").isNotNull()),
        "data_fora_2025": flagged(F.year("_data") == 2025),
        "mes_invalido": flagged(F.trim(F.col("mes")).rlike(r"^[0-9]+$") & F.col("_mes").between(1, 12)),
        "ano_invalido": flagged(F.trim(F.col("ano")).rlike(r"^[0-9]+$") & (F.col("_ano") == 2025)),
        "data_mes_ano_incoerentes": flagged((F.month("_data") == F.col("_mes")) & (F.year("_data") == F.col("_ano"))),
        "municipio_formato_invalido": flagged(F.trim(F.col("municipio_cod")).rlike(r"^31[0-9]{4}$")),
        "risp_invalida": flagged(F.trim(F.col("risp")).rlike(r"^[0-9]+$") & F.col("_risp").between(1, 19)),
        "rmbh_fora_dominio": flagged(F.trim(F.col("rmbh")).isin(RMBH)),
        "categoria_fora_dominio": flagged(F.upper(F.trim(F.col("tentado_consumado"))).isin(source["domain"])),
        "quantidade_invalida": flagged(F.trim(F.col("qtde_vitimas")).rlike(r"^[0-9]+$") & F.col("_q").isNotNull() & (F.col("_q") > 0)),
    })
    return checks

def counts(df, checks):
    return df.agg(*[F.sum(F.when(value, 1).otherwise(0)).alias(key) for key, value in checks.items()]).first().asDict()

def records(df):
    return [row.asDict(recursive=True) for row in df.collect()]

def duplicates(df, keys):
    groups = df.groupBy(*keys).count().filter(F.col("count") > 1)
    totals = groups.agg(F.count("*").alias("grupos"),
                        F.coalesce(F.sum("count"), F.lit(0)).alias("linhas_envolvidas"),
                        F.coalesce(F.sum(F.col("count") - 1), F.lit(0)).alias("linhas_excedentes")).first().asDict()
    totals["exemplos"] = records(groups.orderBy(*keys).limit(10))
    return totals

def normalized(df, columns):
    return df.select(*[(F.upper(F.trim(F.col(c))) if c in ["natureza_delito", "tentado_consumado"]
                       else F.trim(F.col(c))).alias(c) for c in columns])

def geo_conflicts(df):
    grouped = df.groupBy("municipio_cod").agg(*[
        F.sort_array(F.collect_set(c)).alias(c) for c in ["municipio_fato", "risp", "rmbh"]])
    bad = grouped.filter(reduce(lambda a, b: a | b, [F.size(c) > 1 for c in ["municipio_fato", "risp", "rmbh"]]))
    return dict(codigos=bad.count(), exemplos=records(bad.orderBy("municipio_cod").limit(20)))

# COMMAND ----------
# Testes dos controles: dados sintéticos, nunca gravados nas tabelas do projeto.
source = SOURCES[1]
valid = dict(zip(source["columns"], ["310010", "TESTE", "2025-01-01", "1", "2025", "1", "Interior de MG", "TENTADO", "1"]))
cases = [valid,
         {**valid, "data_fato": "2025-02-30", "mes": "2"},
         {**valid, "municipio_cod": None, "qtde_vitimas": "1.5"},
         {**valid, "mes": "2", "qtde_vitimas": "0", "tentado_consumado": "DESCONHECIDO"},
         {**valid, "qtde_vitimas": "9223372036854775808"},
         {**valid, "municipio_cod": "3100100", "risp": "20", "rmbh": "X"},
         {**valid, "municipio_fato": "   "},
         {**valid, "data_fato": "2024-01-01", "ano": "2024"}]
fixture = spark.createDataFrame(cases, StructType([StructField(c, StringType(), True) for c in source["columns"]]))
checked = counts(prepared(fixture), rules(prepared(fixture), source))
expected = {"data_invalida": 1, "quantidade_invalida": 3, "municipio_formato_invalido": 2,
            "ausente__municipio_cod": 1, "ausente__municipio_fato": 1,
            "categoria_fora_dominio": 1, "data_mes_ano_incoerentes": 2,
            "data_fora_2025": 2, "ano_invalido": 1, "risp_invalida": 1, "rmbh_fora_dominio": 1}
require(all(checked[k] == value for k, value in expected.items()), f"Falha nos testes: {checked}")
require(sum(counts(prepared(fixture.limit(1)), rules(prepared(fixture.limit(1)), source)).values()) == 0,
        "Registro válido não deve ser rejeitado")
duplicate_fixture = spark.createDataFrame([valid, valid, {**valid, "municipio_cod": " 310010 "}], fixture.schema)
key = ["municipio_cod", "data_fato", "tentado_consumado"]
require(duplicates(duplicate_fixture, key)["linhas_excedentes"] == 1, "Duplicação bruta não detectada")
require(duplicates(normalized(duplicate_fixture, source["columns"]), key)["linhas_excedentes"] == 2,
        "Colisão após trim não detectada")

# COMMAND ----------
reports = []
geographies = []
for source in SOURCES:
    table = f"workspace.mvp_bronze.{source['name']}"
    version = spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()["version"]
    df = spark.sql(f"SELECT * FROM {table} VERSION AS OF {version}")
    typed = prepared(df)
    checks = rules(typed, source)
    checks["metadados_invalidos"] = flagged(
        present("arquivo_origem") & (F.col("arquivo_sha256") == source["sha256"]) & F.col("ingerido_em").isNotNull())
    errors = counts(typed, checks)
    invalid = typed.filter(reduce(lambda a, b: a | b, checks.values()))
    summary = typed.agg(F.count("*").alias("linhas"), F.sum("_q").alias("soma_vitimas"),
                       F.min("_q").alias("quantidade_minima"), F.max("_q").alias("quantidade_maxima"),
                       F.min("_data").alias("data_minima"), F.max("_data").alias("data_maxima"),
                       F.countDistinct(F.trim("municipio_cod")).alias("municipios")).first().asDict()
    norm = normalized(df, source["columns"])
    key = ["municipio_cod", "data_fato", "tentado_consumado"]
    if "natureza_delito" in source["columns"]:
        key.append("natureza_delito")
    monthly = records(typed.groupBy(F.month("_data").alias("mes")).agg(
        F.count("*").alias("linhas"), F.sum("_q").alias("soma_vitimas")).orderBy("mes"))
    trims = counts(df, {c: F.col(c) != F.trim(F.col(c)) for c in source["columns"]})
    categories = {}
    for c in ["tentado_consumado", "rmbh", "risp"] + (["natureza_delito"] if "natureza_delito" in source["columns"] else []):
        categories[c] = records(typed.groupBy(F.trim(F.col(c)).alias(c)).agg(
            F.count("*").alias("linhas"), F.sum("_q").alias("soma_vitimas")).orderBy(c))
    geo = norm.select("municipio_cod", "municipio_fato", "risp", "rmbh").distinct()
    geographies.append(geo)
    report = dict(tabela=table, versao_delta=int(version), arquivo_sha256=source["sha256"],
                  **summary, erros_por_regra=errors, linhas_com_erro=invalid.count(),
                  exemplos_invalidos=records(invalid.select(*source["columns"]).limit(10)),
                  espacos_externos_por_campo=trims, cobertura_mensal=monthly, categorias=categories,
                  duplicatas_integrais=duplicates(df, source["columns"]),
                  duplicatas_chave_bruta=duplicates(df, key),
                  duplicatas_chave_normalizada=duplicates(norm, key),
                  conflitos_geograficos_internos=geo_conflicts(geo))
    report["baseline_confere"] = summary["linhas"] == source["rows"] and summary["soma_vitimas"] == source["victims"]
    report["cobertura_12_meses"] = [row["mes"] for row in monthly] == list(range(1, 13))
    reports.append(report)
    display(spark.createDataFrame([dict(regra=k, linhas=v) for k, v in errors.items()]))

# COMMAND ----------
combined = geographies[0].unionByName(geographies[1]).distinct()
before = geo_conflicts(combined)
# Simular apenas a regra já documentada; não escrever a Silver nesta etapa.
after_df = combined.withColumn("municipio_fato", F.when(
    (F.col("municipio_cod") == "315990") & F.col("municipio_fato").isin("SANTO ANT DO AMPARO", "SANTO ANTONIO DO AMPARO"),
    F.lit("SANTO ANTONIO DO AMPARO")).otherwise(F.col("municipio_fato")))
after = geo_conflicts(after_df)
blocking = any(r["linhas_com_erro"] > 0 or not r["baseline_confere"] or not r["cobertura_12_meses"] or
               r["duplicatas_integrais"]["grupos"] > 0 or r["duplicatas_chave_normalizada"]["grupos"] > 0 or
               r["conflitos_geograficos_internos"]["codigos"] > 0 for r in reports) or after["codigos"] > 0
result = dict(etapa="qualidade", status="CONCLUIDO", executado_em_utc=datetime.now(timezone.utc).isoformat(),
              testes_sinteticos="APROVADOS", fontes=reports,
              geografia_compartilhada=dict(municipios=combined.select("municipio_cod").distinct().count(),
                                          antes_regra=before, apos_regra=after),
              bloqueios_estruturais=bool(blocking),
              ressalvas=["S/N preservado: semântica não confirmada oficialmente.",
                         "Formato de código municipal validado; sem validação externa contra cadastro oficial.",
                         "Quantitativos publicados não representam pessoas únicas; fontes não podem ser somadas.",
                         "Cobertura dos 12 meses não demonstra ausência de subnotificação."],
              silver_implementada=False)
print(json.dumps(result, ensure_ascii=False, default=str))
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False, default=str))
