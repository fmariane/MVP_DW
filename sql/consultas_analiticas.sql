-- Consultas executadas no Databricks; versões fixadas na evidência.

CREATE OR REPLACE TEMP VIEW a_domestica AS SELECT * FROM workspace.mvp_gold.fato_violencia_domestica VERSION AS OF 0;

CREATE OR REPLACE TEMP VIEW a_feminicidio AS SELECT * FROM workspace.mvp_gold.fato_feminicidio VERSION AS OF 0;

CREATE OR REPLACE TEMP VIEW a_tempo AS SELECT * FROM workspace.mvp_gold.dim_tempo VERSION AS OF 0;

CREATE OR REPLACE TEMP VIEW a_municipio AS SELECT * FROM workspace.mvp_gold.dim_municipio VERSION AS OF 0;

CREATE OR REPLACE TEMP VIEW a_natureza AS SELECT * FROM workspace.mvp_gold.dim_natureza_delito VERSION AS OF 0;

CREATE OR REPLACE TEMP VIEW a_fontes AS SELECT 'Violência doméstica' AS fonte,data_key,municipio_cod,qtde_vitimas FROM a_domestica UNION ALL SELECT 'Feminicídio' AS fonte,data_key,municipio_cod,qtde_vitimas FROM a_feminicidio;


-- q1_mensal
SELECT f.fonte, t.mes, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER (PARTITION BY f.fonte) AS pct_fonte
FROM a_fontes f JOIN a_tempo t USING(data_key)
WHERE t.ano=2025 GROUP BY f.fonte, t.mes ORDER BY f.fonte, t.mes;


-- q2_municipios
WITH agregados AS (
 SELECT f.fonte, m.municipio_cod, m.municipio_nome, SUM(f.qtde_vitimas) AS vitimas
 FROM a_fontes f JOIN a_municipio m USING(municipio_cod)
 GROUP BY f.fonte, m.municipio_cod, m.municipio_nome
)
SELECT *, DENSE_RANK() OVER(PARTITION BY fonte ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER(PARTITION BY fonte) AS pct_fonte
FROM agregados ORDER BY fonte, vitimas DESC, municipio_cod;


-- q2_regioes
WITH agregados AS (
 SELECT f.fonte, m.risp_cod, SUM(f.qtde_vitimas) AS vitimas
 FROM a_fontes f JOIN a_municipio m USING(municipio_cod) GROUP BY f.fonte, m.risp_cod
)
SELECT *, DENSE_RANK() OVER(PARTITION BY fonte ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER(PARTITION BY fonte) AS pct_fonte
FROM agregados ORDER BY fonte, vitimas DESC, CAST(risp_cod AS INT);


-- q3_naturezas
WITH agregados AS (
 SELECT n.natureza_nome, SUM(f.qtde_vitimas) AS vitimas
 FROM a_domestica f JOIN a_natureza n USING(natureza_key) GROUP BY n.natureza_nome
)
SELECT *, DENSE_RANK() OVER(ORDER BY vitimas DESC) AS posicao,
       100.0 * vitimas / SUM(vitimas) OVER() AS pct_fonte
FROM agregados ORDER BY vitimas DESC, natureza_nome;


-- q4_mes_situacao
SELECT t.mes, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY t.mes) AS pct_no_mes
FROM a_feminicidio f JOIN a_tempo t USING(data_key)
GROUP BY t.mes, f.situacao ORDER BY t.mes, f.situacao;


-- q4_regiao_situacao
SELECT m.risp_cod, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY m.risp_cod) AS pct_na_regiao
FROM a_feminicidio f JOIN a_municipio m USING(municipio_cod)
GROUP BY m.risp_cod, f.situacao ORDER BY CAST(m.risp_cod AS INT), f.situacao;


-- q4_regiao_mes_situacao
SELECT m.risp_cod, t.mes, f.situacao, SUM(f.qtde_vitimas) AS vitimas,
       100.0 * SUM(f.qtde_vitimas) / SUM(SUM(f.qtde_vitimas)) OVER(PARTITION BY m.risp_cod,t.mes) AS pct_na_regiao_mes
FROM a_feminicidio f JOIN a_municipio m USING(municipio_cod) JOIN a_tempo t USING(data_key)
GROUP BY m.risp_cod,t.mes,f.situacao ORDER BY CAST(m.risp_cod AS INT),t.mes,f.situacao;
