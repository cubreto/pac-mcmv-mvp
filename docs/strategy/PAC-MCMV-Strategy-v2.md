# Estratégia PAC-MCMV v2.0 - Based on CAIXA Requirements

## 1. Contexto do Projeto

### Objetivo
Desenvolver painéis interativos com IA para análise de projetos do Novo PAC (OGU e FGTS), com foco em:
- Identificação de causas de atraso
- Análise de gargalos por fase (suspensiva, licitação, obras)
- Rankings regionais e por tomador
- Previsão de atrasos antes que ocorram

### Prazo
- **1 mês** para benefícios tangíveis (conforme expectativa CAIXA)

## 2. Arquitetura de Dados

### Sistemas Fonte
- **SIAPF**: Sistema corporativo (atualização D-1)
- **SIIGF**: Sistema corporativo
- **REUNI**: Sistema departamental (atualização 2/2h das 9h às 19h)
- **Bases GEOTR** (SERPRO) e **GEGOV** (REUNI)

### Estrutura dos Dados
- **Granularidade**: Uma linha por operação
- **Histórico**: Limitado (SIAPF tem alguns dados históricos)
- **Campos texto**: Totalmente livres (diagnósticos no REUNI)
- **Qualidade**: Variável, muitos campos com valores nulos

## 3. Requisitos Funcionais Prioritários

### Perguntas de Negócio (1ª versão obrigatória)
1. **Quais as causas de atraso?**
2. **Quais são os gargalos para retirada da cláusula suspensiva?**
3. **Quais são os gargalos para licitação?**
4. **Em que regiões e quais Tomadores têm mais dificuldades?**

### Funcionalidades
- ✅ Dashboards interativos
- ✅ Relatórios PDF programados
- ✅ Chat "pergunte aos dados"
- ✅ Rankings de atrasos (região, contratante, tipo)
- ✅ Previsão de probabilidade de atraso
- ✅ Alertas antecipados por fase

### Fases do Processo PAC
1. **Retirada de Cláusula Suspensiva**
2. **Licitação**
3. **Acompanhamento de Obras**

## 4. Roadmap de Implementação

### Sprint 1: Foundation (Semana 1-2)
- [ ] Setup ambiente AWS com segurança LGPD
- [ ] Análise do arquivo Excel exemplo (REUNI_Operações)
- [ ] Mapeamento de campos críticos
- [ ] Criação schema PostgreSQL baseado nos dados reais

### Sprint 2: ETL & Data Quality (Semana 2-3)
- [ ] ETL para processar Excel do REUNI
- [ ] Validação e limpeza de dados
- [ ] Tratamento de valores nulos
- [ ] Anonimização de dados sensíveis (CPF, etc)

### Sprint 3: Core Analytics (Semana 3-4)
- [ ] Dashboard "Cenário Global da Carteira"
- [ ] Análise por fase (Suspensiva, Licitação, Obras)
- [ ] Rankings e filtros regionais
- [ ] KPIs principais

### Sprint 4: AI Features (Semana 4-5)
- [ ] NLP para análise de campos texto livre
- [ ] Modelo preditivo de atrasos
- [ ] Chat interface com LLM
- [ ] Sistema de alertas

## 5. Arquitetura Técnica

```mermaid
graph TB
    A[REUNI Excel/API] --> B[ETL Python]
    B --> C[PostgreSQL]
    C --> D[FastAPI Backend]
    D --> E[Streamlit Dashboard]
    D --> F[LLM Engine]
    F --> G[Chat Interface]
    E --> H[Users CAIXA/Ministérios]
    G --> H
