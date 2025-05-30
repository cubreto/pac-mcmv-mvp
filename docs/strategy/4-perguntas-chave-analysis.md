# Análise das 4 Perguntas-Chave da CAIXA

## Pergunta 1: Quais as causas de atraso?

### Dados Disponíveis
- Campo "Situação Atual" (texto livre, média 167 caracteres)
- Campo "Suspensiva" (quando preenchido)
- Datas de prazo vs. datas reais

### Estratégia de Extração
```python
# Padrões a buscar no texto
PADROES_ATRASO = [
    "paralisa",
    "atraso",
    "pendente", 
    "falta de",
    "aguardando",
    "impedimento"
]
Métricas Propostas

Top 10 causas mais frequentes
Distribuição por categoria (documento, financeiro, técnico)
Tempo médio por tipo de atraso

Pergunta 2: Gargalos para retirada da cláusula suspensiva
Dados Disponíveis

"Situação da Análise Suspensiva" (6 valores possíveis)
"Data Cumprimento Suspensiva" vs "Vencimento da Suspensiva"
"Qd.Complementações de Suspensiva" (quantidade de idas e vindas)

Análise do Funil
Não enviada (44%) → Em análise (4.8%) → Com pendências (8.3%) → Retirada (40.7%)
Métricas Propostas

Taxa de conversão por etapa
Tempo médio em cada status
Número de complementações necessárias

Pergunta 3: Gargalos para licitação
Dados Disponíveis

"Situação da AIL" (autorização)
"Situação da Análise VRPL"
Datas de publicação de edital

Análise do Funil
Sem AIL (54.7%) → AIL enviada (37.8%) → Edital publicado (4.5%) → VRPL emitida (2.3%)
Métricas Propostas

Taxa de conversão por etapa
Tempo médio entre AIL e publicação
Percentual com VRPL aprovada

Pergunta 4: Regiões e tomadores com dificuldades
Dados Disponíveis

Campo "UF" (27 estados)
Campo "Município Beneficiado" (3,010 municípios)
Campo "Recebedor" (proxy para tomador)

Rankings Propostos

Por Estado: % de obras atrasadas
Por Município: quantidade de pendências
Por Recebedor: tempo médio de execução
Por Valor: correlação tamanho vs atraso

SQL Queries Base
sql-- Q1: Extração será via Python/NLP do campo texto

-- Q2: Funil Suspensiva
SELECT 
    situacao_analise_suspensiva,
    COUNT(*) as total,
    AVG(EXTRACT(DAY FROM (data_cumprimento_suspensiva - vencimento_suspensiva))) as dias_atraso
FROM pac_operations
WHERE situacao_proposta = 'em execucao'
GROUP BY situacao_analise_suspensiva;

-- Q3: Funil Licitação  
SELECT 
    CASE 
        WHEN situacao_analise_vrpl = 'VRPL Emitida' THEN '4. VRPL Emitida'
        WHEN data_publicacao_edital IS NOT NULL THEN '3. Edital Publicado'
        WHEN situacao_ail LIKE '%Autorização Encaminhada%' THEN '2. AIL Autorizada'
        ELSE '1. Aguardando AIL'
    END as etapa_licitacao,
    COUNT(*) as total
FROM pac_operations
GROUP BY etapa_licitacao
ORDER BY etapa_licitacao;

-- Q4: Ranking Regional
SELECT 
    uf,
    COUNT(*) as total_operacoes,
    SUM(CASE WHEN /* critério de atraso */ THEN 1 ELSE 0 END) as operacoes_atrasadas,
    AVG(percentual_realizado_reuni) as percentual_medio
FROM pac_operations
GROUP BY uf
ORDER BY operacoes_atrasadas DESC;
Visualizações Propostas
Dashboard 1: Visão Geral

Cards com totais
Gráfico de pizza por status
Mapa de calor por UF

Dashboard 2: Análise de Atrasos

Word cloud de causas
Timeline de atrasos
Top 10 problemas

Dashboard 3: Funis de Processo

Funil suspensiva
Funil licitação
Tempo médio por fase

Dashboard 4: Rankings

Tabela por UF
Tabela por recebedor
Filtros interativos


Análise baseada em 4,899 registros do REUNI
