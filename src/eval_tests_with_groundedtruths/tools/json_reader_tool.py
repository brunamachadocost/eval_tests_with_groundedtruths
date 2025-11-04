import json
import os
from typing import List, Dict, Any, Tuple
from crewai.tools import BaseTool
from pydantic import Field

from ..models.evaluation_models import ResponseData, GroundTruthData


class JSONFileReaderTool(BaseTool):
    name: str = "JSON File Reader Tool"
    description: str = (
        "Ferramenta para ler e carregar arquivos JSON das pastas de respostas "
        "e gabaritos, fazendo o matching por ID entre os arquivos."
    )

    def _run(self, files_dir: str = "files", groundtruths_dir: str = "groundedtruths") -> Dict[str, Any]:
        """
        Lê arquivos JSON das pastas especificadas e faz matching por ID.
        
        Args:
            files_dir: Diretório com arquivos de resposta
            groundtruths_dir: Diretório com arquivos de gabarito
            
        Returns:
            Dicionário com arquivos encontrados e pares matcheados
        """
        try:
            # Ler arquivos de resposta
            response_files = self._load_json_files(files_dir, ResponseData)
            
            # Ler arquivos de gabarito  
            groundtruth_files = self._load_json_files(groundtruths_dir, GroundTruthData)
            
            # Fazer matching por ID
            matched_pairs = self._match_files_by_id(response_files, groundtruth_files)
            print(f"[MATCHED] = {matched_pairs}")
            
            result = {
                "response_files_count": len(response_files),
                "groundtruth_files_count": len(groundtruth_files),
                "matched_pairs_count": len(matched_pairs),
                "response_files": [{"id": r.id, "agent_name": r.agent_name} for r in response_files],
                "groundtruth_files": [{"id": g.id, "description": g.description} for g in groundtruth_files],
                "matched_pairs": matched_pairs,
                "unmatched_responses": [r.id for r in response_files if not any(r.id == pair[0].id for pair in matched_pairs)],
                "unmatched_groundtruths": [g.id for g in groundtruth_files if not any(g.id == pair[1].id for pair in matched_pairs)]
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Erro ao processar arquivos JSON: {str(e)}"}
    
    def _load_json_files(self, directory: str, model_class) -> List[Any]:
        """Carrega todos os arquivos JSON de um diretório usando o modelo especificado."""
        files = []
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Diretório {directory} não encontrado")
            
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        validated_data = model_class(**data)
                        files.append(validated_data)
                except Exception as e:
                    print(f"Erro ao processar arquivo {filepath}: {e}")
                    continue
                    
        return files
    
    def _match_files_by_id(self, responses: List[ResponseData], groundtruths: List[GroundTruthData]) -> List[Tuple[ResponseData, GroundTruthData]]:
        """Faz o matching entre arquivos de resposta e gabarito pelo ID."""
        matched_pairs = []
        
        for response in responses:
            for groundtruth in groundtruths:
                if response.id == groundtruth.id:
                    matched_pairs.append((response, groundtruth))
                    break
                    
        return matched_pairs
