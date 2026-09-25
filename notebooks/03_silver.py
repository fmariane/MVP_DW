# Databricks notebook source
# MAGIC %md
# MAGIC # Silver — PCMG 2025
# MAGIC Tipagem e padronização com valores brutos preservados. Candidatos e rejeições
# MAGIC são reconciliados antes de publicar. Uma reexecução valida o snapshot existente.

# COMMAND ----------
import json
import uuid
from datetime import datetime, timezone
from functools import reduce
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StringType, StructField, StructType

spark.conf.set("spark.sql.session.timeZone", "UTC")
RULE_VERSION = "silver_v1"
EXECUTION = str(uuid.uuid4())
COMMON = ["municipio_cod", "municipio_fato", "data_fato", "mes", "ano", "risp", "rmbh"]
META = ["arquivo_origem", "arquivo_sha256", "ingerido_em"]
SOURCES = [
    dict(name="violencia_domestica_2025", rows=117169, victims=162032,
         sha256="0d6e677ab65e7d04834904080ec0296eccf8dabd6013fe45910c9d754f94b4fe",
         columns=COMMON + ["natureza_delito", "tentado_consumado", "qtde_vitimas"], domain=["S", "N"]),
    dict(name="feminicidio_2025", rows=381, victims=391,
         sha256="364dec0197c1d9c40a050883573ce22efd280a43114680fc1491e40db6e89630",
         columns=COMMON + ["tentado_consumado", "qtde_vitimas"], domain=["TENTADO", "CONSUMADO"]),
]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def key(source):
    return ["municipio_cod", "data_fato", "tentado_consumado"] + (["natureza_delito"] if "natureza_delito" in source["columns"] else [])

def missing(c):
    return F.col(c).isNull() | (F.trim(F.col(c)) == "")

def fail(valid):
    return ~F.coalesce(valid, F.lit(False))

def prepare(raw, source, version):
    df = raw.select(*source["columns"], *META)
    for field, dtype in [("data_fato", "DATE"), ("mes", "INT"), ("ano", "INT"), ("risp", "INT"), ("qtde_vitimas", "BIGINT")]:
        df = df.withColumn(f"_{field}", F.expr(f"try_cast(trim({field}) AS {dtype})"))
    q_valid = F.coalesce(F.trim(F.col("qtde_vitimas")).rlike(r"^[0-9]+$") & (F.col("_qtde_vitimas") > 0), F.lit(False))
    checks = {f"ausente__{c}": missing(c) for c in source["columns"]}
    checks.update({
        "data_invalida": fail(F.trim(F.col("data_fato")).rlike(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$") & F.col("_data_fato").isNotNull()),
        "data_fora_2025": fail(F.year("_data_fato") == 2025),
        "mes_invalido": fail(F.trim(F.col("mes")).rlike(r"^[0-9]+$") & F.col("_mes").between(1, 12)),
        "ano_invalido": fail(F.trim(F.col("ano")).rlike(r"^[0-9]+$") & (F.col("_ano") == 2025)),
        "data_mes_ano_incoerentes": fail((F.month("_data_fato") == F.col("_mes")) & (F.year("_data_fato") == F.col("_ano"))),
        "municipio_invalido": fail(F.trim(F.col("municipio_cod")).rlike(r"^31[0-9]{4}$")),
        "risp_invalida": fail(F.trim(F.col("risp")).rlike(r"^[0-9]+$") & F.col("_risp").between(1, 19)),
        "rmbh_invalida": fail(F.trim(F.col("rmbh")).isin("Interior de MG", "Belo Horizonte", "RMBH (Sem BH)")),
        "categoria_invalida": fail(F.upper(F.trim(F.col("tentado_consumado"))).isin(source["domain"])),
        "quantidade_invalida": ~q_valid,
        "metadados_invalidos": missing("arquivo_origem") | fail(F.col("arquivo_sha256") == source["sha256"]) | F.col("ingerido_em").isNull(),
        "duplicata_integral_bruta": F.count(F.lit(1)).over(Window.partitionBy(*source["columns"])) > 1,
    })
    reasons = F.filter(F.array(*[F.when(expr, F.lit(name)) for name, expr in checks.items()]), lambda x: x.isNotNull())
    fields = []
    for c in source["columns"]:
        if c in ["data_fato", "mes", "ano", "qtde_vitimas"]:
            expr = F.col(f"_{c}")
        elif c in ["tentado_consumado", "natureza_delito"]:
            expr = F.upper(F.trim(F.col(c)))
        else:
            expr = F.trim(F.col(c))
        if c == "municipio_fato":
            expr = F.when((F.trim(F.col("municipio_cod")) == "315990") & (expr == "SANTO ANT DO AMPARO"),
                          F.lit("SANTO ANTONIO DO AMPARO")).otherwise(expr)
        fields.append(expr.alias(c))
    out = df.select(*fields, F.struct(*[F.col(c) for c in source["columns"]]).alias("dados_brutos"), *META,
                    F.lit(f"workspace.mvp_bronze.{source['name']}").alias("tabela_bronze"),
                    F.lit(version).cast("long").alias("versao_bronze"),
                    F.lit(RULE_VERSION).alias("versao_regras"), F.current_timestamp().alias("tratado_em"),
                    q_valid.alias("_quantidade_valida"), reasons.alias("motivos_rejeicao"))
    return out.withColumn("motivos_rejeicao", F.when(
        F.count(F.lit(1)).over(Window.partitionBy(*key(source))) > 1,
        F.concat(F.col("motivos_rejeicao"), F.array(F.lit("chave_operacional_duplicada"))))
        .otherwise(F.col("motivos_rejeicao")))

def metrics(df):
    return df.agg(F.count("*").alias("linhas"),
                  F.coalesce(F.sum(F.when(F.col("_quantidade_valida"), F.col("qtde_vitimas"))), F.lit(0)).alias("soma_quantidades_validas"),
                  F.coalesce(F.sum(F.when(~F.col("_quantidade_valida"), 1).otherwise(0)), F.lit(0)).alias("quantidades_invalidas")).first().asDict()

def reconcile(df):
    valid = df.filter(F.size("motivos_rejeicao") == 0)
    rejected = df.filter(F.size("motivos_rejeicao") > 0)
    entry, output, quarantine = metrics(df), metrics(valid), metrics(rejected)
    for metric in entry:
        require(entry[metric] == output[metric] + quarantine[metric], f"Falha na reconciliação: {metric}")
    return valid, rejected, dict(entrada=entry, candidatos=output, rejeitados=quarantine)

def same_content(left, right, columns):
    return left.select(*columns).exceptAll(right.select(*columns)).limit(1).count() == 0 and right.select(*columns).exceptAll(left.select(*columns)).limit(1).count() == 0

def validate_stored(stored, candidate, source):
    require(stored.columns == candidate.columns, "Colunas Silver diferentes do contrato")
    require([(f.name, f.dataType.simpleString()) for f in stored.schema] ==
            [(f.name, f.dataType.simpleString()) for f in candidate.schema], "Tipos Silver diferentes do contrato")
    stable = [c for c in candidate.columns if c != "tratado_em"]
    require(same_content(stored, candidate, stable), "Silver existente difere do candidato; publicação bloqueada")
    require(stored.filter(F.col("tratado_em").isNull()).count() == 0, "Timestamp de tratamento ausente")
    require(stored.groupBy(*key(source)).count().filter(F.col("count") > 1).count() == 0, "Duplicidade na Silver")

# COMMAND ----------
# Testar tratamento, rejeições e conservação antes de processar as fontes.
s = SOURCES[1]
good = dict(zip(s["columns"], ["315990", " SANTO ANT DO AMPARO ", "2025-01-01", "1", "2025", "6", "Interior de MG", " tentado ", "2"]))
def fixture(rows):
    return (spark.createDataFrame(rows, StructType([StructField(c, StringType(), True) for c in s["columns"]]))
            .withColumn("arquivo_origem", F.lit("teste"))
            .withColumn("arquivo_sha256", F.lit(s["sha256"]))
            .withColumn("ingerido_em", F.current_timestamp()))
cases = [good, {**good, "data_fato": "2025-02-30", "qtde_vitimas": "3"},
         {**good, "data_fato": "2025-01-02", "qtde_vitimas": "1.5"},
         {**good, "data_fato": "2025-01-03", "municipio_cod": None},
         {**good, "data_fato": "2025-01-04", "qtde_vitimas": "9223372036854775808"}]
test_valid, test_rejected, test_totals = reconcile(prepare(fixture(cases), s, 0))
require(test_totals["entrada"] == dict(linhas=5, soma_quantidades_validas=7, quantidades_invalidas=2), "Totais sintéticos incorretos")
require(test_totals["candidatos"]["linhas"] == 1 and test_totals["rejeitados"]["linhas"] == 4, "Partição de rejeições incorreta")
row = test_valid.first()
require(row.municipio_fato == "SANTO ANTONIO DO AMPARO" and row.tentado_consumado == "TENTADO" and row.qtde_vitimas == 2,
        "Padronização sintética incorreta")
require(row.dados_brutos.municipio_fato == good["municipio_fato"], "Valor bruto modificado")
_, _, collision = reconcile(prepare(fixture([good, {**good, "municipio_cod": " 315990 "}]), s, 0))
require(collision["rejeitados"]["linhas"] == 2, "Todas as linhas de chave duplicada devem ser rejeitadas")

# COMMAND ----------
prepared = []
for source in SOURCES:
    table = f"workspace.mvp_bronze.{source['name']}"
    version = int(spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()["version"])
    raw = spark.sql(f"SELECT * FROM {table} VERSION AS OF {version}")
    prepared.append((source, raw, prepare(raw, source, version), version))

# Conflitos compartilhados rejeitam todas as linhas do município envolvido.
geo_cols = ["municipio_cod", "municipio_fato", "risp", "rmbh"]
geo = reduce(lambda a, b: a.unionByName(b), [df.select(*geo_cols) for _, _, df, _ in prepared])
bad_geo = geo.groupBy("municipio_cod").agg(*[F.countDistinct(c).alias(c) for c in geo_cols[1:]])
bad_geo = bad_geo.filter(reduce(lambda a, b: a | b, [F.col(c) > 1 for c in geo_cols[1:]])).select("municipio_cod").withColumn("_conflito_geo", F.lit(True))
geo_conflicts = bad_geo.count()
staged = []
for source, raw, df, version in prepared:
    df = (df.join(bad_geo, "municipio_cod", "left")
          .withColumn("motivos_rejeicao", F.when(F.col("_conflito_geo"),
              F.concat(F.col("motivos_rejeicao"), F.array(F.lit("conflito_geografico"))))
              .otherwise(F.col("motivos_rejeicao"))).drop("_conflito_geo"))
    valid, rejected, totals = reconcile(df)
    audit_table = f"workspace.mvp_silver.rejeicoes_{source['name']}"
    audit = rejected.withColumn("execucao_id", F.lit(EXECUTION))
    if not spark.catalog.tableExists(audit_table):
        audit.write.format("delta").mode("error").saveAsTable(audit_table)
    elif totals["rejeitados"]["linhas"]:
        audit.write.format("delta").mode("append").saveAsTable(audit_table)
    require(spark.table(audit_table).filter(F.col("execucao_id") == EXECUTION).count() == totals["rejeitados"]["linhas"],
            "Falha ao persistir rejeições desta execução")
    candidate = valid.drop("_quantidade_valida", "motivos_rejeicao")
    changes = candidate.agg(*[F.sum(F.when(~F.col(c).cast("string").eqNullSafe(F.col(f"dados_brutos.{c}")), 1).otherwise(0)).alias(c)
                              for c in source["columns"]]).first().asDict()
    staged.append((source, raw, candidate, totals, audit_table, changes, version))

# Todos os gates são avaliados antes da criação de qualquer tabela de negócio.
require(geo_conflicts == 0, "Conflitos geográficos: consulte as rejeições")
for source, raw, candidate, totals, _, _, _ in staged:
    require(totals["rejeitados"]["linhas"] == 0, f"Rejeições em {source['name']}; publicação bloqueada")
    require(totals["entrada"] == dict(linhas=source["rows"], soma_quantidades_validas=source["victims"], quantidades_invalidas=0), "Baseline divergente")
    require(same_content(raw, candidate.select("dados_brutos.*"), source["columns"]), "Conteúdo bruto não preservado")
    if "natureza_delito" in source["columns"]:
        require(candidate.select("natureza_delito").distinct().count() == 174, "Inventário de naturezas alterado")
    table = f"workspace.mvp_silver.{source['name']}"
    if spark.catalog.tableExists(table):
        validate_stored(spark.table(table), candidate, source)

# COMMAND ----------
reports = []
for source, raw, candidate, totals, audit_table, changes, version in staged:
    table = f"workspace.mvp_silver.{source['name']}"
    if spark.catalog.tableExists(table):
        action = "snapshot_existente_validado"
    else:
        candidate.write.format("delta").mode("error").saveAsTable(table)
        action = "criada"
    stored = spark.table(table)
    validate_stored(stored, candidate, source)
    output = stored.agg(F.count("*").alias("linhas"), F.sum("qtde_vitimas").alias("soma_vitimas")).first().asDict()
    require(output == dict(linhas=source["rows"], soma_vitimas=source["victims"]), "Reconciliação pós-gravação falhou")
    detail = spark.sql(f"DESCRIBE DETAIL {table}").select("format", "id").first().asDict()
    require(detail["format"] == "delta", "Formato deve ser Delta")
    reports.append(dict(tabela=table, acao=action, arquivo_sha256=source["sha256"], versao_bronze=version,
                        reconciliacao=totals, persistido=output, alteracoes_textuais_por_campo=changes,
                        tabela_rejeicoes=audit_table, dados_brutos_preservados=True,
                        duplicatas_chave=0, formato=detail["format"], delta_id=detail["id"],
                        tipos={f.name: f.dataType.simpleString() for f in stored.schema}))
    display(stored.limit(10))

result = dict(etapa="silver", status="APROVADO", execucao_id=EXECUTION, versao_regras=RULE_VERSION,
              executado_em_utc=datetime.now(timezone.utc).isoformat(), testes_sinteticos="APROVADOS",
              conflitos_geograficos=geo_conflicts, fontes=reports,
              ressalvas=["S/N preservado sem interpretação.", "Fontes separadas; quantitativos não representam pessoas únicas."])
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))
