from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class ResponseData(BaseModel):
    """Estrutura dos JSONs de resposta dos agents"""
    id: str = Field(..., description="Identificador único da resposta")
    agent_name: Optional[str] = Field(None, description="Nome do agent que gerou a resposta")
    response_data: Dict[str, Any] = Field(..., description="Dados da resposta do agent")
    file_name: Optional[str] = Field(None, description="Nome do arquivo processado (para OCR)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais (para OCR)")
    timestamp: Optional[datetime] = Field(None, description="Timestamp de quando a resposta foi gerada")


class GroundTruthData(BaseModel):
    """Estrutura dos JSONs de gabarito"""
    id: str = Field(..., description="Identificador único correspondente à resposta")
    expected_response: Dict[str, Any] = Field(..., description="Resposta esperada/gabarito")
    file_name: Optional[str] = Field(None, description="Nome do arquivo processado (para OCR)")
    description: Optional[str] = Field(None, description="Descrição opcional do caso de teste")


class ExactMatchResult(BaseModel):
    """Resultado da avaliação de match exato"""
    id: str = Field(..., description="Identificador único da avaliação")
    total_fields: int = Field(..., description="Total de campos avaliados")
    matching_fields: int = Field(..., description="Número de campos que fizeram match exato")
    accuracy_percentage: float = Field(..., description="Percentual de acurácia (0-100)")
    mismatched_fields: Dict[str, Dict[str, Any]] = Field(..., description="Campos que não fizeram match - formato: {campo: {expected, actual}}")


class EvaluationSummary(BaseModel):
    """Resumo consolidado da avaliação"""
    total_evaluations: int = Field(..., description="Total de avaliações realizadas")
    overall_accuracy: float = Field(..., description="Acurácia geral do sistema (0-100)")
    perfect_matches: int = Field(..., description="Número de matches perfeitos (100% de acerto)")
    partial_matches: int = Field(..., description="Número de matches parciais (>0% e <100%)")
    complete_mismatches: int = Field(..., description="Número de falhas completas (0% de acerto)")
    common_error_patterns: List[str] = Field(..., description="Padrões de erro mais comuns identificados")


class EvaluationState(BaseModel):
    """Estado do flow de avaliação"""
    response_files: List[str] = Field(default_factory=list, description="Lista de arquivos de resposta encontrados", exclude= True)
    groundtruth_files: List[str] = Field(default_factory=list, description="Lista de arquivos de gabarito encontrados", exclude= True)
    matched_pairs: List[tuple] = Field(default_factory=list, description="Pares de arquivos (resposta, gabarito, exclude= True) com mesmo ID", exclude= True)
    evaluation_results: List[ExactMatchResult] = Field(default_factory=list, description="Resultados das avaliações individuais", exclude= True)
    summary: Optional[EvaluationSummary] = Field(None, description="Resumo consolidado da avaliação", exclude= True)
    report_generated: bool = Field(False, description="Flag indicando se o relatório foi gerado", exclude= True)
