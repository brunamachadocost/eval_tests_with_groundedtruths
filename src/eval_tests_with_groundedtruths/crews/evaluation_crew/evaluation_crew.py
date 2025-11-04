from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from ...tools.json_reader_tool import JSONFileReaderTool
from ...tools.exact_match_tool import ExactMatchTool
from ...tools.report_generator_tool import ReportGeneratorTool


@CrewBase
class EvaluationCrew:
    """Crew para avaliação de agents com gabaritos"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def file_scanner(self) -> Agent:
        return Agent(
            config=self.agents_config["file_scanner"],
            tools=[JSONFileReaderTool()],
            verbose=True,
            llm="anthropic/claude-sonnet-4-20250514"
        )

    @agent
    def exact_match_evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config["exact_match_evaluator"],
            tools=[ExactMatchTool()],
            verbose=True,
            llm="anthropic/claude-sonnet-4-20250514"
        )

    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["report_generator"],
            tools=[ReportGeneratorTool()],
            verbose=True,
            llm="anthropic/claude-sonnet-4-20250514"
        )

    @task
    def scan_and_load_files(self) -> Task:
        return Task(
            config=self.tasks_config["scan_and_load_files"],
        )

    @task
    def evaluate_exact_match(self) -> Task:
        return Task(
            config=self.tasks_config["evaluate_exact_match"],
        )

    @task
    def generate_evaluation_report(self) -> Task:
        return Task(
            config=self.tasks_config["generate_evaluation_report"],
        )

    @crew
    def crew(self) -> Crew:
        """Cria a Crew de Avaliação"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
