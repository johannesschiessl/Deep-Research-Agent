from typing import List, Tuple
import os
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

from utils.file_utils import create_run_directory, save_plan_to_json

class ResearchStep(BaseModel):
    """A single step in the research plan"""
    instruction: str = Field(..., description="Detailed instruction of what needs to be researched")
    expected_outcome: str = Field(..., description="What information or insights this step should yield")

class ResearchPlan(BaseModel):
    """The complete research plan"""
    query: str = Field(..., description="The original research query")
    reasoning: str = Field(..., description="The planner's reasoning about how to approach the research")
    steps: List[ResearchStep] = Field(..., description="The ordered steps to conduct the research")
    run_id: str | None = Field(None, description="Unique identifier for this research run")

class PlannerAgent:
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.client = OpenAI(api_key=api_key)

    def create_initial_plan(self, query: str) -> Tuple[ResearchPlan, Path]:
        """Create an initial research plan based on the user's query and save it"""
        run_dir, run_id = create_run_directory()
        
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
                                "expected_outcome": "what this step should yield"
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
        
        plan = response.choices[0].message.parsed
        
        plan_dict = plan.model_dump()
        plan_dict["query"] = query
        plan_dict["run_id"] = run_id
        final_plan = ResearchPlan(**plan_dict)
        
        save_plan_to_json(final_plan, run_dir)
        
        return final_plan, run_dir
