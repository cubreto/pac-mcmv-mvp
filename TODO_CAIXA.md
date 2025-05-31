# TODO: CAIXA Dashboard Improvements

## ✅ Completed (Dashboard V2)
- [x] Text analysis for delay causes (Question 1)
- [x] Suspensivas bottleneck analysis (Question 2)
- [x] Geographic/regional rankings (Question 4)
- [x] Real data integration (4,899 REUNI operations)

## 🔄 In Progress
- [ ] Licitação funnel analysis (Question 3)
  - [ ] Track AIL (Autorização para Início de Licitação) status
  - [ ] Track VRPL (Verificação do Resultado do Processo Licitatório)
  - [ ] Create funnel visualization: Sem AIL → AIL enviada → Edital → VRPL
  - [ ] Calculate conversion rates between stages

## 📋 Next Steps
1. Add missing columns to dashboard:
   - situacao_da_ail
   - situacao_da_analise_vrpl
   - data_publicacao_edital_licitacao

2. Create licitação funnel chart in new tab

3. Test with Docker:
   ```bash
   docker-compose -f docker-compose.dev.yml up

Deploy to production environment

🐛 Known Issues

Database has 2 different credential sets (need to consolidate)
Some date columns may need better parsing
Text analysis could use more sophisticated NLP

📊 KPIs to Track (from meeting)

Causas de atraso ✅
Gargalos suspensiva ✅
Gargalos licitação ⚠️
Ranking regional ✅
