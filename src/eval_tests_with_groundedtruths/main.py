#!/usr/bin/env python
import os
from crewai.flow import Flow, listen, start
from crewai import LLM

from eval_tests_with_groundedtruths.models.evaluation_models import EvaluationState
from eval_tests_with_groundedtruths.crews.evaluation_crew.evaluation_crew import EvaluationCrew


class AgentEvaluationFlow(Flow[EvaluationState]):
    """Flow para avaliação de agents com gabaritos"""

    @start()
    def start_evaluation(self):
        """Inicia o processo de avaliação"""
        print("🚀 Iniciando processo de avaliação de agents com gabaritos...")
        
        # Verificar se as pastas existem
        if not os.path.exists("files"):
            print("❌ Pasta 'files' não encontrada")
            return
        
        if not os.path.exists("groundedtruths"):
            print("❌ Pasta 'groundedtruths' não encontrada")
            return
        
        print("✅ Pastas de arquivos encontradas")
        print("📁 Iniciando escaneamento de arquivos...")

    @listen(start_evaluation)
    def run_evaluation_crew(self):
        """Executa a crew de avaliação completa"""
        print("🤖 Executando crew de avaliação...")
        
        try:
            # Criar e executar a crew de avaliação
            evaluation_crew = EvaluationCrew()
            result = evaluation_crew.crew().kickoff()
            
            print("✅ Crew de avaliação executada com sucesso!")
            print(f"📄 Resultado: {result.raw}")
            
            # Marcar como concluído
            self.state.report_generated = True
            
        except Exception as e:
            print(f"❌ Erro na execução da crew: {str(e)}")
            raise

    @listen(run_evaluation_crew)
    def finalize_evaluation(self):
        """Finaliza o processo de avaliação"""
        if self.state.report_generated:
            print("🎉 Processo de avaliação concluído com sucesso!")
            print("📋 Relatório gerado: EVALUATION_REPORT.md")
            print("💡 Verifique o arquivo para ver os resultados detalhados")
        else:
            print("⚠️ Processo de avaliação não foi concluído corretamente")


def kickoff():
    """Executa o flow de avaliação"""
    evaluation_flow = AgentEvaluationFlow()
    evaluation_flow.kickoff()


def plot():
    """Gera o plot do flow de avaliação"""
    evaluation_flow = AgentEvaluationFlow()
    evaluation_flow.plot()


if __name__ == "__main__":
    kickoff()
