# Relatório de Avaliação de Agents

**Data/Hora**: 2025-11-04 09:18:09  
**Total de Avaliações**: 3

## 📊 Resumo Quantitativo

| Métrica | Valor |
|---------|-------|
| **Acurácia Geral** | 55.55% |
| **Matches Perfeitos** | 1 (33.3%) |
| **Matches Parciais** | 2 (66.7%) |
| **Falhas Completas** | 0 (0.0%) |

## 🎯 Análise Qualitativa

### Performance Geral
**REGULAR - O agent precisa de ajustes significativos.**

### Principais Achados
- Taxa de acerto perfeito: 33.3%
- Acurácia média geral: 55.6%

### Recomendações
- Revisar prompts e instruções dos agents
- Implementar validação de saída mais rigorosa
- Investigar padrões de erro específicos
- Considerar fine-tuning ou ajuste de parâmetros
- Aumentar conjunto de dados de teste para melhor cobertura

## 🔍 Padrões de Erro Identificados

### Campos com mais erros:
  • confidence: 2 ocorrências
  • response: 2 ocorrências
### Tipos de erro mais comuns:
  • Campo 'confidence': divergência numérica: 2 ocorrências
  • Campo 'response': divergência textual: 2 ocorrências

## 📋 Detalhamento por Avaliação

| ID | Acurácia | Campos Corretos | Total Campos | Status |
|-----|----------|----------------|--------------|---------|
| 001 | 33.33% | 1 | 3 | ⚠️ Parcial |
| 002 | 100.0% | 3 | 3 | ✅ Perfeito |
| 003 | 33.33% | 1 | 3 | ⚠️ Parcial |

## 🔧 Campos com Divergências

### Avaliação 001
- **confidence**
  - Esperado: `0.9`
  - Obtido: `0.85`

- **response**
  - Esperado: `O produto chegará entre 3 a 5 dias úteis`
  - Obtido: `O produto chegará em 3-5 dias úteis`

### Avaliação 003
- **confidence**
  - Esperado: `0.65`
  - Obtido: `0.6`

- **response**
  - Esperado: `O produto chegará em 1 dias úteis`
  - Obtido: `O produto chegará em 10 dias úteis`


---
*Relatório gerado automaticamente pelo sistema de avaliação de agents*
