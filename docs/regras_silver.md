# Regras de tratamento — Silver PCMG 2025

Contrato `silver_v1`, definido após os controles do item 10 e implementado no
[notebook Silver](../notebooks/03_silver.py). Execução e reconciliação dos itens
14–15 comprovadas no [relatório Silver](reconciliacao_silver.md).

## Destinos e rastreabilidade

Manter duas tabelas independentes: `workspace.mvp_silver.violencia_domestica_2025`
e `workspace.mvp_silver.feminicidio_2025`. Uma linha conserva a granularidade
publicada; não se afirma que represente uma ocorrência ou pessoa distinta.

Preservar todos os campos originais em uma coluna `dados_brutos` do tipo STRUCT,
com os valores de texto da Bronze, além de `arquivo_origem`, `arquivo_sha256`,
`ingerido_em`, nome da tabela Bronze e `versao_bronze`. Registrar também
`tratado_em` em UTC e a versão das regras. Os campos tratados ficam em colunas
próprias, permitindo comparação com `dados_brutos`.

## Regras por campo

| Campo | Tipo e tratamento | Controle e decisão |
| --- | --- | --- |
| municipio_cod | STRING; remover espaços externos | Exigir seis dígitos, prefixo 31 no recorte de MG. Não acrescentar dígito, converter em número ou alegar validação contra cadastro externo. |
| municipio_fato | STRING; remover espaços externos | Nome não vazio. Aplicar somente a correspondência explícita do código 315990 descrita abaixo. |
| data_fato | DATE após remoção de espaços externos | Exigir formato AAAA-MM-DD, data válida e ano 2025. Não inferir nem corrigir datas impossíveis. |
| mes | INT | Exigir texto com dígitos, valor 1–12 e correspondência com data_fato. Não substituir silenciosamente o mês informado pelo derivado. |
| ano | INT | Exigir texto com dígitos, valor 2025 e correspondência com data_fato. |
| risp | STRING; remover espaços externos | Validar representação inteira e domínio 1–19. Não atribuir nomes às regiões sem fonte. |
| rmbh | STRING; remover espaços externos | Domínio: `Interior de MG`, `Belo Horizonte`, `RMBH (Sem BH)`. |
| natureza_delito | STRING; remover espaços externos e converter para maiúsculas | Exclusiva da violência doméstica; manter acentos e espaços internos. Exigir valor não vazio, inventariar categorias e verificar colisões após normalização. |
| tentado_consumado | STRING; remover espaços externos e converter para maiúsculas | Doméstica: S/N, sem tradução. Feminicídio: TENTADO/CONSUMADO. Não harmonizar os dois domínios. |
| qtde_vitimas | BIGINT | Exigir texto composto de dígitos e inteiro positivo dentro da capacidade do tipo. Rejeitar frações, overflow, nulos, zero e negativos para revisão; não arredondar. |

Todos os campos originais são obrigatórios para estes snapshots. `NULL`, texto
vazio e texto apenas com espaços são ausências. Não preencher com zero,
"desconhecido", média ou valor da linha anterior. Valores ausentes recebem motivo
explícito de rejeição. Códigos fora do domínio também exigem revisão.

## Padronização municipal explícita

Somente para `municipio_cod = '315990'`, após trim, transformar
`SANTO ANT DO AMPARO` em `SANTO ANTONIO DO AMPARO`; manter a forma completa
quando já presente. O nome completo vem da própria publicação, não de uma
validação externa. Outros nomes para esse código não são sobrescritos
automaticamente. Guardar o nome original em `dados_brutos.municipio_fato`.

Validar por código os atributos nome, RISP e RMBH dentro e entre as duas fontes,
após essa regra. Conflitos remanescentes bloqueiam a publicação até investigação;
não selecionar `first`, `max` ou um nome arbitrário para escondê-los.

## Duplicidades e normalização

Verificar linhas integrais e estas chaves operacionais, antes e depois do tratamento:

- Doméstica: municipio_cod + data_fato + natureza_delito + tentado_consumado.
- Feminicídio: municipio_cod + data_fato + tentado_consumado.

Não executar `dropDuplicates`, somar grupos repetidos ou escolher uma linha.
Se uma chave aparecer mais de uma vez, registrar todas as linhas do grupo para
investigação e bloquear a publicação. A mesma regra vale para colisões criadas
por trim, maiúsculas ou conversão de data. A quantidade de linhas excedentes
é apenas um indicador diagnóstico, não uma instrução de exclusão.

Categorias novas devem ser comparadas com o inventário e a versão da fonte.
O total de 174 naturezas é referência destes snapshots, não limite universal.
Quantidades elevadas não são removidas como outliers: valores fora da faixa
observada requerem revisão da publicação, não truncamento automático.

## Rejeições e reconciliação

Na implementação, construir candidatos e rejeições antes de publicar a Silver.
Cada rejeição deve preservar `dados_brutos`, rastreabilidade e uma lista de
`motivos_rejeicao`. Uma linha com vários motivos é contada uma vez no total
de rejeitados, embora figure em vários contadores de regra. Persistir os
registros rejeitados em tabela de auditoria identificada pela execução.

Critérios de aceitação:

1. Linhas de entrada = linhas candidatas válidas + linhas rejeitadas.
2. Para valores numéricos válidos, soma de entrada = soma candidata + soma das
   rejeições com quantidade válida. Contabilizar separadamente quantidades
   inválidas; não convertê-las em zero para fechar a reconciliação.
3. Para os snapshots atuais, publicar somente com zero rejeições, sem conflitos
   geográficos e sem chaves duplicadas após todos os tratamentos.
4. Totais esperados: doméstica 117169 linhas / soma 162032; feminicídio
   381 linhas / soma 391, vinculados aos hashes da Bronze.
5. Manter as fontes separadas. Nunca calcular um total combinado de vítimas.
6. Validar candidatos antes da gravação e reler as tabelas persistidas para
   repetir os controles. Uma falha não deve substituir uma versão aprovada.
7. Reexecução do mesmo snapshot não pode acumular linhas. Versão nova da fonte
   exige reconciliação e aprovação das novas referências antes da publicação.

O código S/N desconhecido não é uma ausência: é um valor publicado válido
cuja interpretação está pendente. Ele deve permanecer disponível na Silver,
com essa ressalva documentada, sem impedir as perguntas atuais do MVP.

## Limites

A consistência estrutural não comprova completude epidemiológica, ausência de
subnotificação ou unicidade de pessoas. Ter registros em todos os meses não
transforma automaticamente uma ausência municipal em zero. Uma revisão futura
da fonte pode exigir novas regras e novas referências.
