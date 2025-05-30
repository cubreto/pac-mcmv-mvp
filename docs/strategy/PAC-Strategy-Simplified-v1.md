# Estratégia PAC Dashboard - Versão Simplificada

## Objetivo
Desenvolver dashboard para análise do Novo PAC com foco em identificar atrasos e gargalos em 1 mês.

## Escopo Confirmado

### Dados
- **Fonte**: Arquivos Excel do REUNI (já temos exemplo com 4,899 registros)
- **Atualização**: A cada 2 horas
- **Estrutura**: 1 linha por operação

### 4 Perguntas-Chave da CAIXA
1. Quais as causas de atraso?
2. Quais os gargalos para retirada da cláusula suspensiva?
3. Quais os gargalos para licitação?
4. Quais regiões/tomadores têm mais dificuldades?

## Plano de 4 Semanas

### Semana 1: Fundação
- [ ] Carregar Excel REUNI no PostgreSQL
- [ ] Dashboard básico com métricas gerais
- [ ] Identificar campos para as 4 perguntas

### Semana 2: Análise de Texto
- [ ] Extrair insights do campo "Situação Atual"
- [ ] Categorizar causas de atraso
- [ ] Primeiros KPIs das 4 perguntas

### Semana 3: Dashboards Completos
- [ ] Funil de cláusula suspensiva
- [ ] Funil de licitação
- [ ] Rankings regionais
- [ ] Exportação PDF

### Semana 4: Entrega e Refinamento
- [ ] Interface de chat simples
- [ ] Testes com usuários
- [ ] Ajustes finais
- [ ] Deploy em produção

## Decisões Técnicas

### Stack Confirmado
- Backend: Python + PostgreSQL
- Frontend: Streamlit
- NLP: Biblioteca simples (spaCy/NLTK)
- Deploy: Docker na AWS

### Fora do Escopo v1
- Integração em tempo real com sistemas
- Modelo complexo de ML
- Autenticação avançada

## Definição de Sucesso
- Dashboard funcionando com dados reais
- Responde as 4 perguntas da CAIXA
- Reduz tempo de análise de horas para minutos

---
*Baseado na reunião de 21/05/2025*
