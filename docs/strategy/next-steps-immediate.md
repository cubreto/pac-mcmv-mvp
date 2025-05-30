# Próximos Passos Imediatos - PAC Dashboard

## Esta Semana (Semana 1)

### Segunda-feira
- [ ] Confirmar entendimento dos campos com CAIXA
- [ ] Analisar Portaria 32/2024 para regras de atraso

### Terça-feira  
- [ ] Criar schema PostgreSQL baseado no Excel REUNI
- [ ] Desenvolver ETL básico para carga inicial

### Quarta-feira
- [ ] Subir dados no banco
- [ ] Criar queries para as 4 perguntas

### Quinta-feira
- [ ] Desenvolver dashboard básico no Streamlit
- [ ] Implementar filtros por UF e período

### Sexta-feira
- [ ] Testar extração de texto do campo "Situação Atual"
- [ ] Preparar demo para CAIXA

## Perguntas para CAIXA

1. **Acesso aos dados**
   - Como receberemos os arquivos a cada 2h?
   - Existe API ou será SFTP/email?

2. **Portaria 32/2024**
   - Podem compartilhar o documento?
   - Quais são os critérios exatos?

3. **Campos sensíveis**
   - Quais campos precisam anonimização?
   - CPF aparece em algum campo?

4. **Usuários**
   - Quantos usuários simultâneos?
   - Perfis diferentes de acesso?

5. **Baseline atual**
   - Quanto tempo leva hoje para gerar um relatório?
   - Qual o processo atual?

## Entregas da Semana 1

1. **Dashboard v0.1** com:
   - Total de operações
   - Distribuição por UF
   - Status das propostas
   - Valores totais

2. **Documento de análise**:
   - Mapeamento dos campos
   - Identificação de dados faltantes
   - Plano para extrair as 4 respostas

3. **Protótipo NLP**:
   - 10 exemplos de extração de causa
   - Categorias propostas

---
*Atualizado: 21/05/2025*
