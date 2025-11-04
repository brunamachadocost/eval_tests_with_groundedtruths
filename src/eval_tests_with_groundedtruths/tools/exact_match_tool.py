from typing import Dict, Any
from crewai.tools import BaseTool
from pydantic import Field

from ..models.evaluation_models import ResponseData, GroundTruthData, ExactMatchResult


class ExactMatchTool(BaseTool):
    name: str = "Exact Match Evaluation Tool"
    description: str = (
        "Ferramenta para avaliar a precisão exata comparando respostas de agents "
        "com gabaritos campo por campo, calculando percentuais de acerto."
    )

    def _run(self, response_data: Dict[str, Any], groundtruth_data: Dict[str, Any], evaluation_id: str) -> Dict[str, Any]:
        """
        Compara dados de resposta com gabarito usando match exato.
        
        Args:
            response_data: Dados da resposta do agent (response_data do ResponseData)
            groundtruth_data: Dados esperados do gabarito (expected_response do GroundTruthData)
            evaluation_id: ID único da avaliação
            
        Returns:
            Resultado da avaliação de match exato
        """
        try:
            # Inicializar contadores
            total_fields = 0
            matching_fields = 0
            mismatched_fields = {}
            
            # Obter todos os campos únicos dos dois objetos
            all_fields = set(response_data.keys()) | set(groundtruth_data.keys())
            total_fields = len(all_fields)
            
            # Comparar cada campo
            for field in all_fields:
                response_value = response_data.get(field)
                expected_value = groundtruth_data.get(field)
                
                if self._values_match(response_value, expected_value):
                    matching_fields += 1
                else:
                    mismatched_fields[field] = {
                        "expected": expected_value,
                        "actual": response_value
                    }
            
            # Calcular percentual de acurácia
            accuracy_percentage = (matching_fields / total_fields * 100) if total_fields > 0 else 0
            
            # Criar resultado estruturado
            result = ExactMatchResult(
                id=evaluation_id,
                total_fields=total_fields,
                matching_fields=matching_fields,
                accuracy_percentage=round(accuracy_percentage, 2),
                mismatched_fields=mismatched_fields
            )
            
            return {
                "success": True,
                "evaluation_result": result.dict(),
                "summary": f"Avaliação ID {evaluation_id}: {matching_fields}/{total_fields} campos corretos ({accuracy_percentage:.1f}% acurácia)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na avaliação de match exato: {str(e)}",
                "evaluation_id": evaluation_id
            }
    
    def _values_match(self, value1: Any, value2: Any) -> bool:
        """
        Compara dois valores para verificar se fazem match exato.
        
        Args:
            value1: Primeiro valor para comparação
            value2: Segundo valor para comparação
            
        Returns:
            True se os valores fazem match exato, False caso contrário
        """
        # Tratamento para valores None
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False
            
        # Tratamento para strings (case-insensitive e trim)
        if isinstance(value1, str) and isinstance(value2, str):
            return value1.strip().lower() == value2.strip().lower()
        
        # Tratamento para números (com tolerância para floats)
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            if isinstance(value1, float) or isinstance(value2, float):
                return abs(float(value1) - float(value2)) < 1e-10
            return value1 == value2
            
        # Tratamento para listas
        if isinstance(value1, list) and isinstance(value2, list):
            if len(value1) != len(value2):
                return False
            for v1, v2 in zip(value1, value2):
                if not self._values_match(v1, v2):
                    return False
            return True
            
        # Tratamento para dicionários
        if isinstance(value1, dict) and isinstance(value2, dict):
            if set(value1.keys()) != set(value2.keys()):
                return False
            for key in value1.keys():
                if not self._values_match(value1[key], value2[key]):
                    return False
            return True
        
        # Comparação direta para outros tipos
        return value1 == value2
