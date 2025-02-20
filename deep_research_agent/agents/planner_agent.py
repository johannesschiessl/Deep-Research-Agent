from typing import List
import os
from pydantic import BaseModel, Field
from openai import OpenAI

class ResearchStep(BaseModel):
    """A single step in the research plan"""
    instruction: str = Field(..., description="Detailed instruction of what needs to be researched")
    expected_outcome: str = Field(..., description="What information or insights this step should yield")

class ResearchPlan(BaseModel):
    """The complete research plan"""
    reasoning: str = Field(..., description="The planner's reasoning about how to approach the research")
    steps: List[ResearchStep] = Field(..., description="The ordered steps to conduct the research")

class PlannerAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def create_initial_plan(self, query: str) -> ResearchPlan:
        """Create an initial research plan based on the user's query"""
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            response_format=ResearchPlan,
            messages=[
                {
                    "role": "developer",
                    "content": """You are an expert research planner. Your task is to create a detailed research plan based on the user's query.
                    The plan should include your reasoning about how to approach the research and a series of concrete steps.
                    Each step should have a clear purpose and expected outcome.
                    
                    Format your response as a JSON object with the following structure:
                    {
                        "reasoning": "your thought process about how to approach the research",
                        "steps": [
                            {
                                "instruction": "detailed instruction of what needs to be researched",
                                "expected_outcome": "what this step should yield",
                            },
                            ...
                        ]
                    }"""
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )

        return response.choices[0].message.parsed
