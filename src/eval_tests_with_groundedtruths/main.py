#!/usr/bin/env python
import os
from random import randint

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from crewai import LLM

from eval_tests_with_groundedtruths.crews.poem_crew.poem_crew import PoemCrew


class PoemState(BaseModel):
    sentence_count: int = 1
    poem: str = ""

# Light Agent/Agente atomico executado fora da crew
SearcherSpecialist = Agent(
    role="Searcher Specialist", 
    goal="",
    backstory="",
    tools=[]
)


llm = LLM(
        model="openai/openai/gpt-4o",
        base_url=f'{os.getenv("BASE_URL_ASIMOV")}/v2',
        api_key=os.getenv("ASIMOV_TOKEN"),
        temperature=0.3,
        # top_p=top_p,
        # n=n,
        # max_tokens=max_tokens,
    )

 

class EvalTestsWithGroundedtruthFlow(Flow):

    @start
    def run(self):
        self.state.temperature = None

    @listen(run)
    def get_wheather(self):
        agent = SearcherSpecialist("whats the weather in tokyo?")
        result = agent.kickoff()


        # self.state.temperature = self.get_temperature()

    def get_temperature(self):
        return 20

    ###############################

    @start()
    def generate_sentence_count(self):
        print("Generating sentence count")
        self.state.sentence_count = randint(1, 5)

    @listen(generate_sentence_count)
    def generate_poem(self):
        print("Generating poem")
        result = (
            PoemCrew()
            .crew()
            .kickoff(inputs={"sentence_count": self.state.sentence_count})
        )

        print("Poem generated", result.raw)
        self.state.poem = result.raw

    @listen(generate_poem)
    def save_poem(self):
        print("Saving poem")
        with open("poem.txt", "w") as f:
            f.write(self.state.poem)


def kickoff():
    poem_flow = EvalTestsWithGroundedtruthFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = EvalTestsWithGroundedtruthFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
