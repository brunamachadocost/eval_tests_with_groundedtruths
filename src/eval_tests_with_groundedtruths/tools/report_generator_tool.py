from typing import List, Dict, Any
from datetime import datetime
from crewai.tools import BaseTool
from collections import Counter

from ..models.evaluation_models import ExactMatchResult, EvaluationSummary


class ReportGeneratorTool(BaseTool):
    name: str = "Evaluation Report Generator Tool"
    description: str = (
        "Ferramenta para gerar relatórios consolidados de avaliação de agents, "
        "incluindo análises quantitativas e qualitativas dos resultados."
    )

    def _run(self, evaluation_results: List[Dict[str, Any]], output_file: str = "EVALUATION_REPORT.md") -> Dict[str, Any]:
        """
        Gera relatório consolidado das avaliações de agents.
        
        Args:
            evaluation_results: Lista de resultados de avaliação (ExactMatchResult.dict())
            output_file: Nome do arquivo de saída para o relatório
            
        Returns:
            Resultado da geração do relatório
        """
        try:
            # Converter dicts de volta para objetos ExactMatchResult para análise
            results = []
            for result_dict in evaluation_results:
                if isinstance(result_dict, dict) and 'evaluation_result' in result_dict:
                    result_data = result_dict['evaluation_result']
                    results.append(ExactMatchResult(**result_data))
                elif isinstance(result_dict, dict):
                    results.append(ExactMatchResult(**result_dict))
            
            if not results:
                return {
                    "success": False,
                    "error": "Nenhum resultado de avaliação fornecido"
                }
            
            # Gerar análise consolidada
            summary = self._generate_summary(results)
            
            # Gerar análise qualitativa
            qualitative_analysis = self._generate_qualitative_analysis(results)
            
            # Gerar relatório em markdown
            report_content = self._generate_markdown_report(summary, qualitative_analysis, results)
            
            # Salvar arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return {
                "success": True,
                "summary": summary.dict(),
                "qualitative_analysis": qualitative_analysis,
                "report_file": output_file,
                "total_evaluations": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na geração do relatório: {str(e)}"
            }
    
    def _generate_summary(self, results: List[ExactMatchResult]) -> EvaluationSummary:
        """Gera resumo quantitativo das avaliações."""
        total_evaluations = len(results)
        
        # Calcular acurácia geral
        total_accuracy = sum(result.accuracy_percentage for result in results)
        overall_accuracy = total_accuracy / total_evaluations if total_evaluations > 0 else 0
        
        # Categorizar resultados
        perfect_matches = sum(1 for result in results if result.accuracy_percentage == 100)
        complete_mismatches = sum(1 for result in results if result.accuracy_percentage == 0)
        partial_matches = total_evaluations - perfect_matches - complete_mismatches
        
        # Identificar padrões de erro comuns
        common_error_patterns = self._identify_error_patterns(results)
        
        return EvaluationSummary(
            total_evaluations=total_evaluations,
            overall_accuracy=round(overall_accuracy, 2),
            perfect_matches=perfect_matches,
            partial_matches=partial_matches,
            complete_mismatches=complete_mismatches,
            common_error_patterns=common_error_patterns
        )
    
    def _identify_error_patterns(self, results: List[ExactMatchResult]) -> List[str]:
        """Identifica padrões de erro mais comuns."""
        error_fields = []
        error_types = []
        
        for result in results:
            for field, mismatch in result.mismatched_fields.items():
                error_fields.append(field)
                
                expected = mismatch.get('expected')
                actual = mismatch.get('actual')
                
                if expected is None and actual is not None:
                    error_types.append(f"Campo '{field}': valor não esperado fornecido")
                elif expected is not None and actual is None:
                    error_types.append(f"Campo '{field}': valor esperado ausente")
                elif isinstance(expected, str) and isinstance(actual, str):
                    error_types.append(f"Campo '{field}': divergência textual")
                elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                    error_types.append(f"Campo '{field}': divergência numérica")
                else:
                    error_types.append(f"Campo '{field}': divergência de tipo/formato")
        
        # Contar ocorrências
        field_counter = Counter(error_fields)
        type_counter = Counter(error_types)
        
        patterns = []
        
        # Top 5 campos com mais erros
        if field_counter:
            patterns.append("Campos com mais erros:")
            for field, count in field_counter.most_common(5):
                patterns.append(f"  • {field}: {count} ocorrências")
        
        # Top 5 tipos de erro mais comuns
        if type_counter:
            patterns.append("Tipos de erro mais comuns:")
            for error_type, count in type_counter.most_common(5):
                patterns.append(f"  • {error_type}: {count} ocorrências")
        
        return patterns
    
    def _generate_qualitative_analysis(self, results: List[ExactMatchResult]) -> Dict[str, Any]:
        """Gera análise qualitativa dos resultados."""
        analysis = {
            "performance_assessment": "",
            "key_findings": [],
            "recommendations": []
        }
        
        total = len(results)
        perfect_rate = sum(1 for r in results if r.accuracy_percentage == 100) / total * 100
        overall_avg = sum(r.accuracy_percentage for r in results) / total
        
        # Avaliação geral de performance
        if overall_avg >= 90:
            analysis["performance_assessment"] = "EXCELENTE - O agent demonstra alta precisão e consistência."
        elif overall_avg >= 75:
            analysis["performance_assessment"] = "BOM - O agent apresenta boa performance com espaço para melhorias."
        elif overall_avg >= 50:
            analysis["performance_assessment"] = "REGULAR - O agent precisa de ajustes significativos."
        else:
            analysis["performance_assessment"] = "CRÍTICO - O agent requer revisão completa da implementação."
        
        # Principais achados
        analysis["key_findings"].append(f"Taxa de acerto perfeito: {perfect_rate:.1f}%")
        analysis["key_findings"].append(f"Acurácia média geral: {overall_avg:.1f}%")
        
        if perfect_rate < 30:
            analysis["key_findings"].append("Baixa taxa de acertos perfeitos indica problemas sistemáticos")
        
        # Recomendações
        if overall_avg < 75:
            analysis["recommendations"].append("Revisar prompts e instruções dos agents")
            analysis["recommendations"].append("Implementar validação de saída mais rigorosa")
        
        if perfect_rate < 50:
            analysis["recommendations"].append("Investigar padrões de erro específicos")
            analysis["recommendations"].append("Considerar fine-tuning ou ajuste de parâmetros")
        
        analysis["recommendations"].append("Aumentar conjunto de dados de teste para melhor cobertura")
        
        return analysis
    
    def _generate_markdown_report(self, summary: EvaluationSummary, qualitative: Dict[str, Any], results: List[ExactMatchResult]) -> str:
        """Gera o conteúdo do relatório em formato Markdown."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Relatório de Avaliação de Agents

**Data/Hora**: {timestamp}  
**Total de Avaliações**: {summary.total_evaluations}

## 📊 Resumo Quantitativo

| Métrica | Valor |
|---------|-------|
| **Acurácia Geral** | {summary.overall_accuracy}% |
| **Matches Perfeitos** | {summary.perfect_matches} ({summary.perfect_matches/summary.total_evaluations*100:.1f}%) |
| **Matches Parciais** | {summary.partial_matches} ({summary.partial_matches/summary.total_evaluations*100:.1f}%) |
| **Falhas Completas** | {summary.complete_mismatches} ({summary.complete_mismatches/summary.total_evaluations*100:.1f}%) |

## 🎯 Análise Qualitativa

### Performance Geral
**{qualitative['performance_assessment']}**

### Principais Achados
"""
        
        for finding in qualitative['key_findings']:
            report += f"- {finding}\n"
        
        report += f"""
### Recomendações
"""
        
        for rec in qualitative['recommendations']:
            report += f"- {rec}\n"
        
        report += f"""
## 🔍 Padrões de Erro Identificados

"""
        
        for pattern in summary.common_error_patterns:
            if pattern.endswith(':'):
                report += f"### {pattern}\n"
            else:
                report += f"{pattern}\n"
        
        report += f"""
## 📋 Detalhamento por Avaliação

| ID | Acurácia | Campos Corretos | Total Campos | Status |
|-----|----------|----------------|--------------|---------|
"""
        
        for result in results:
            status = "✅ Perfeito" if result.accuracy_percentage == 100 else (
                "⚠️ Parcial" if result.accuracy_percentage > 0 else "❌ Falha"
            )
            report += f"| {result.id} | {result.accuracy_percentage}% | {result.matching_fields} | {result.total_fields} | {status} |\n"
        
        report += f"""
## 🔧 Campos com Divergências

"""
        
        for result in results:
            if result.mismatched_fields:
                report += f"### Avaliação {result.id}\n"
                for field, mismatch in result.mismatched_fields.items():
                    expected = mismatch.get('expected', 'N/A')
                    actual = mismatch.get('actual', 'N/A')
                    report += f"- **{field}**\n"
                    report += f"  - Esperado: `{expected}`\n"
                    report += f"  - Obtido: `{actual}`\n"
                    report += f"\n"
        
        report += f"""
---
*Relatório gerado automaticamente pelo sistema de avaliação de agents*
"""
        
        return report
