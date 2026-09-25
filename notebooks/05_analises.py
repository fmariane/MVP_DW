# Databricks notebook source
# MAGIC %md
# MAGIC # Consultas analíticas — quatro perguntas, MG 2025
# MAGIC SUM(qtde_vitimas) mede quantitativos publicados, não pessoas distintas.
# MAGIC Fontes e denominadores permanecem separados. Leituras Gold versionadas.

# COMMAND ----------
import json
from datetime import datetime, timezone
from pyspark.sql import functions as F

spark.conf.set("spark.sql.session.timeZone", "UTC")
names = {"domestica": "fato_violencia_domestica", "feminicidio": "fato_feminicidio",
         "tempo": "dim_tempo", "municipio": "dim_municipio", "natureza": "dim_natureza_delito"}
lineage = []
for alias, name in names.items():
    table = f"workspace.mvp_gold.{name}"
    version = int(spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()["version"])
    spark.sql(f"SELECT * FROM {table} VERSION AS OF {version}").createOrReplaceTempView(f"a_{alias}")
    lineage.append(dict(tabela=table, versao_delta=version))
spark.sql("""SELECT 'Violência doméstica' AS fonte, data_key, municipio_cod, qtde_vitimas FROM a_domestica
             UNION ALL
             SELECT 'Feminicídio' AS fonte, data_key, municipio_cod, qtde_vitimas FROM a_feminicidio""").createOrReplaceTempView("a_fontes")

QUERIES = {
"q1_mensal": """
SELECT f.fonte, t.mes, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER (PARTITION BY f.fonte) AS pct_fonte
FROM a_fontes f JOIN a_tempo t USING(data_key)
WHERE t.ano=2025 GROUP BY f.fonte, t.mes ORDER BY f.fonte, t.mes
""",
"q2_municipios": """
WITH agregados AS (
 SELECT f.fonte, m.municipio_cod, m.municipio_nome, SUM(f.qtde_vitimas) AS vitimas
 FROM a_fontes f JOIN a_municipio m USING(municipio_cod)
 GROUP BY f.fonte, m.municipio_cod, m.municipio_nome
)
SELECT *, DENSE_RANK() OVER(PARTITION BY fonte ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER(PARTITION BY fonte) AS pct_fonte
FROM agregados ORDER BY fonte, vitimas DESC, municipio_cod
""",
"q2_regioes": """
WITH agregados AS (
 SELECT f.fonte, m.risp_cod, SUM(f.qtde_vitimas) AS vitimas
 FROM a_fontes f JOIN a_municipio m USING(municipio_cod) GROUP BY f.fonte, m.risp_cod
)
SELECT *, DENSE_RANK() OVER(PARTITION BY fonte ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER(PARTITION BY fonte) AS pct_fonte
FROM agregados ORDER BY fonte, vitimas DESC, CAST(risp_cod AS INT)
""",
"q3_naturezas": """
WITH agregados AS (
 SELECT n.natureza_nome, SUM(f.qtde_vitimas) AS vitimas
 FROM a_domestica f JOIN a_natureza n USING(natureza_key) GROUP BY n.natureza_nome
)
SELECT *, DENSE_RANK() OVER(ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER() AS pct_fonte
FROM agregados ORDER BY vitimas DESC, natureza_nome
""",
"q4_mes_situacao": """
SELECT t.mes, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY t.mes) AS pct_no_mes
FROM a_feminicidio f JOIN a_tempo t USING(data_key)
GROUP BY t.mes, f.situacao ORDER BY t.mes, f.situacao
""",
"q4_regiao_situacao": """
SELECT m.risp_cod, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY m.risp_cod) AS pct_na_regiao
FROM a_feminicidio f JOIN a_municipio m USING(municipio_cod)
GROUP BY m.risp_cod, f.situacao ORDER BY CAST(m.risp_cod AS INT), f.situacao
""",
"q4_regiao_mes_situacao": """
SELECT m.risp_cod, t.mes, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY m.risp_cod,t.mes) AS pct_na_regiao_mes
FROM a_feminicidio f JOIN a_municipio m USING(municipio_cod) JOIN a_tempo t USING(data_key)
GROUP BY m.risp_cod,t.mes,f.situacao ORDER BY CAST(m.risp_cod AS INT),t.mes,f.situacao
"""
}

# COMMAND ----------
expected = {"Violência doméstica": 162032, "Feminicídio": 391}
results = {}
for name, sql in QUERIES.items():
    frame = spark.sql(sql)
    rows = [r.asDict() for r in frame.collect()]
    for row in rows:
        for field in list(row):
            if field.startswith("pct_"):
                row[field] = float(row[field])
    if "fonte" in frame.columns:
        totals = {r["fonte"]: int(r["total"]) for r in frame.groupBy("fonte").agg(F.sum("vitimas").alias("total")).collect()}
        assert totals == expected, (name, totals)
        for source in expected:
            assert abs(sum(r["pct_fonte"] for r in rows if r["fonte"] == source) - 100) < 0.0001
    else:
        assert sum(r["vitimas"] for r in rows) == (162032 if name == "q3_naturezas" else 391), name
    if name.startswith("q4_"):
        keys = [k for k in ["risp_cod", "mes"] if k in frame.columns]
        groups = {}
        percent = next(k for k in frame.columns if k.startswith("pct_"))
        for row in rows:
            key = tuple(row[k] for k in keys)
            groups[key] = groups.get(key, 0) + row[percent]
        assert all(abs(value - 100) < 0.0001 for value in groups.values()), name
    results[name] = rows
    print(name)
    display(frame)
assert len(results["q1_mensal"]) == 24
assert len(results["q3_naturezas"]) == 174
assert {r["situacao"] for r in results["q4_mes_situacao"]} == {"TENTADO", "CONSUMADO"}

# COMMAND ----------
report = dict(etapa="analises", status="APROVADO", executado_em_utc=datetime.now(timezone.utc).isoformat(),
              fontes_gold=lineage, totais_por_fonte=expected, consultas=QUERIES, resultados=results,
              controles="Totais e denominadores percentuais reconciliados",
              limitacoes=["Quantitativos publicados, não pessoas distintas.", "Fontes não somadas.",
                          "Rankings de volume, não risco por habitante.", "Um ano não comprova sazonalidade recorrente.",
                          "Ausências de combinações não imputadas como zero.", "S/N doméstico não traduzido."])
dbutils.notebook.exit(json.dumps(report, ensure_ascii=False))
