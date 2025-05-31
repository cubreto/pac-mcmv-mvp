# Notas da Reunião com CAIXA - Novo PAC Dashboard
**Data:** 21/05/2025  
**Participantes:** [A definir]  
**Projeto:** Dashboard Novo PAC - OGU e FGTS

## 1. Fontes de Dados Confirmadas

### Sistemas Fonte
- **Obras Públicas**: 
  - SIAPF (Sistema principal)
  - SIIGF 
  - REUNI
  - Bases SERPRO/GEGOV
  
- **Habitação (FGTS)**: 
  - SIAPF
  - REUNI

### Frequência de Atualização
- **Consolidado "Novo PAC OGU"**: Publicado a cada 2 horas (9h às 19h)
- **Formato**: Exportações CSV/XLSX geradas por GEOTR/GEGOV

## 2. Estrutura dos Dados

### Granularidade
- **1 linha = 1 operação** (sem histórico na base atual)
- Não há versionamento/histórico nas exportações

### Campo de Texto Livre
- **Diagnósticos no REUNI**: Texto totalmente livre
- Densidade e frequência variáveis
- Principal fonte para análise de causas

## 3. Definições de Negócio

### Definição Formal de Atraso
- **Portaria Conjunta 32/2024**: Define obras paralisadas
- **SA161**: Específico para FGTS
- Necessário codificar estas regras no ETL

## 4. KPIs Prioritários (Prazo: 1 mês)

1. **Causas de atraso** (extrair do texto livre)
2. **Gargalos para retirada de cláusula suspensiva**
3. **Gargalos em licitação**
4. **Ranking de atrasos por região/tomador**

## 5. Funcionalidades Requeridas

### Entregáveis
- Dashboards interativos
- Relatórios PDF programados
- Chat "pergunte aos dados"

### Recursos Avançados
- Predição de atrasos
- Alertas por fase
- Análise preditiva

## 6. Segurança e Compliance

- Dados majoritariamente públicos
- Existem campos sensíveis que requerem anonimização
- Conformidade com LGPD obrigatória

## 7. Métricas de Sucesso

### ROI Principal
- Redução do tempo de obtenção de informações para CAIXA/Ministérios/Casa Civil
- Métrica proposta: "minutos-para-informe"
- Necessário capturar baseline atual

## 8. Decisões Técnicas

### ETL
- Começar com exportações CSV/XLSX
- Programar ingestas a cada 2 horas
- Validação contra esquema "1 operação por linha"

### Análise de Texto
- Foco no campo "Situação Atual"
- Implementar regras de limpeza
- Usar embeddings para categorização

### Arquitetura
- Manter Streamlit para dashboards
- Adicionar exportação PDF
- Integrar LLM para chat em v2

## 9. Próximos Passos Acordados

1. [ ] Obter acesso às exportações GEOTR/GEGOV
2. [ ] Analisar Portaria 32/2024 e SA161
3. [ ] Protótipo com dados reais em 1 semana
4. [ ] Demonstração de KPIs prioritários em 2 semanas

---
**Anotado por:** [Nome]  
**Revisado por:** [Nome]  
**Status:** Confirmado
