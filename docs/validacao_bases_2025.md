# Validação inicial das bases de 2025

Inspeção local realizada em 22/09/2026. Fontes preservadas sem alterações. Esta verificação não substitui os controles e evidências da execução no Databricks.

## Proveniência

- [Conjunto PCMG](https://dados.mg.gov.br/pt_PT/dataset/violencia-contra-mulher).
- [Recurso feminicídios 2025](https://dados.mg.gov.br/pt_PT/dataset/violencia-contra-mulher/resource/1afc4e40-3e53-49ce-96a1-f0df6a625459).
- [Recurso violência doméstica 2025](https://dados.mg.gov.br/pt_PT/dataset/violencia-contra-mulher/resource/b339e530-586f-4128-81d0-7a327ff20b7e).
- Dicionário consultado: `datapackage.json`, recursos `feminicidio-2025` e `violencia-contra-mulher-2025`.
- Licença declarada dos dados: CC BY 4.0. Não confundir com a licença do código do projeto.
- Arquivos disponibilizados localmente pelo usuário. Data de download informada pelo usuário na checklist: 22/09/2026. A inspeção também ocorreu em 22/09/2026.
- A correspondência binária entre os arquivos locais e os downloads atuais do portal não foi verificada. Os hashes abaixo identificam as cópias inspecionadas.

## Resultados locais

| Verificação | Feminicídios | Violência doméstica |
| --- | ---: | ---: |
| Linhas | 381 | 117.169 |
| Colunas | 9 | 10 |
| Municípios presentes | 183 | 853 |
| Soma de qtde_vitimas | 391 | 162.032 |
| Mínimo e máximo de qtde_vitimas | 1 a 2 | 1 a 31 |
| Período observado | 01/01/2025 a 31/12/2025 | 01/01/2025 a 31/12/2025 |
| Meses presentes | 12 | 12 |
| Campos nulos ou vazios | 0 | 0 |
| Linhas integralmente duplicadas | 0 | 0 |
| Datas inválidas em AAAA-MM-DD | 0 | 0 |
| Divergências entre data e mês/ano | 0 | 0 |

Ambos são CSVs delimitados por ponto e vírgula, lidos como UTF-8 com suporte a BOM. A presença dos 12 meses não prova que todos os eventos reais foram registrados ou que a fonte não sofrerá revisões.

## Granularidade: o que foi comprovado e o que permanece limitado

Não há identificador de pessoa ou ocorrência nos campos publicados. O dicionário define `qtde_vitimas` como quantidade de vítimas, mas não declara uma chave primária nem garante pessoas únicas.

As seguintes combinações são únicas nas cópias locais, com zero repetições:

- Feminicídios: município + data do fato + tentado/consumado.
- Violência doméstica: município + data do fato + natureza do delito + código S/N.

Essas combinações serão a granularidade operacional observada para o modelo. A estrutura é compatível com quantitativos agrupados nessas dimensões; a unicidade observada não prova a regra de agregação da fonte nem que uma linha represente uma ocorrência. Revalidar as chaves a cada carga e não eliminar repetições futuras automaticamente.

## Códigos: validação semântica

Na base de feminicídios, o campo contém rótulos explícitos TENTADO e CONSUMADO, coerentes com a descrição do dicionário. As somas são 213 e 178, respectivamente.

Na base de violência doméstica, há S e N. O dicionário informa somente “Tentado ou consumado”, sem explicitar a correspondência. A soma associada a S é 161.004 e a N é 1.028. Frequências não comprovam significado: NÃO converter S/N para consumado/tentado por inferência.

**Pendência:** localizar um dicionário oficial ou confirmação do publicador que documente S/N. Até lá, preservar o valor bruto; se houver campo descritivo na Silver, usar “Significado não confirmado”. As perguntas do MVP não dependem da resolução dessa pendência.

## Comparabilidade e sobreposição

Há campos comuns de município, data, mês, ano, RISP e RMBH. São duas medidas publicadas em conjuntos com definições e metodologias próprias. Não há chave de ligação entre eventos ou pessoas; portanto, não é possível verificar sobreposição nem construir uma trajetória individual entre as bases.

Manter duas fatos e comparar agregados territoriais e temporais, sem somar fontes ou calcular uma suposta proporção de violência que se converteu em feminicídio. Preservar códigos municipais como identificadores de texto; não pressupor equivalência com códigos de outras fontes sem tabela de correspondência.

## Próximas verificações

- Confirmar o significado oficial de S/N, sem bloquear as perguntas atuais.
- Relações municipais verificadas na modelagem: uma divergência de nome no código 315990, sem conflitos de RISP/RMBH. Regra de padronização documentada em modelagem_dimensional.md.
- Implementar os controles no pipeline e reconciliar linhas e somas em cada camada.
- Documentar as versões e possíveis revisões da fonte.

## Identificação das cópias locais (SHA-256)

- `feminicidio_2025.csv`: `364dec0197c1d9c40a050883573ce22efd280a43114680fc1491e40db6e89630`
- `violencia_domestica_2025.csv`: `0d6e677ab65e7d04834904080ec0296eccf8dabd6013fe45910c9d754f94b4fe`
- `datapackage.json`: `9eb2f45753289ea8367a39754c12928da881e19249f2ab557e74887256ec33fa`
