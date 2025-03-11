import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

from agents.planner_agent import ResearchPlan
from agents.search_agent import SearchResult

class ResearchReport(BaseModel):
    """Comprehensive research report based on all collected data"""
    title: str = Field(..., description="Title of the research report")
    executive_summary: str = Field(..., description="Brief executive summary of the research findings")
    introduction: str = Field(..., description="Introduction to the research topic")
    methodology: str = Field(..., description="Methodology used in the research")
    findings: List[Dict[str, str]] = Field(..., description="Key findings of the research")
    conclusions: str = Field(..., description="Conclusions drawn from the research")
    references: List[Dict[str, str]] = Field(default_factory=list, description="References used in the research")

class ReportAgent:
    """Agent responsible for generating a comprehensive research report"""
    
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.client = OpenAI(api_key=api_key)
    
    def _collect_all_data(self, plan: ResearchPlan, search_results: List[SearchResult]) -> Dict[str, Any]:
        """Collect all data from the research process"""
        all_data = {
            "query": plan.query,
            "reasoning": plan.reasoning,
            "steps": [],
            "citations": []
        }
        
        for result in search_results:
            step_data = {
                "step_number": result.step_number,
                "instruction": result.step_instruction,
                "search_query": result.search_query,
                "summary": result.summary
            }
            all_data["steps"].append(step_data)
            
            for citation in result.citations:
                if citation not in all_data["citations"] and "url" in citation and citation["url"]:
                    all_data["citations"].append(citation)
        
        return all_data
    
    def generate_report(self, plan: ResearchPlan, search_results: List[SearchResult]) -> str:
        """Generate a comprehensive research report based on all collected data"""
        print("Generating research report...")
        
        all_data = self._collect_all_data(plan, search_results)
        
        context = f"""
        RESEARCH QUERY: {all_data['query']}
        
        RESEARCH REASONING: {all_data['reasoning']}
        
        RESEARCH STEPS AND FINDINGS:
        """
        
        for step in all_data["steps"]:
            context += f"""
            STEP {step['step_number']}: {step['instruction']}
            SEARCH QUERY: {step['search_query']}
            SUMMARY: {step['summary']}
            ---
            """
        
        if all_data["citations"]:
            context += "\nCITATIONS:\n"
            for citation in all_data["citations"]:
                context += f"- {citation.get('title', 'No title')}: {citation.get('url', 'No URL')}\n"
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert research report writer. Your task is to create a comprehensive research report based on the data collected.
                    The report should include:
                    1. Title
                    2. Executive Summary
                    3. Introduction
                    4. Methodology
                    5. Findings
                    6. Conclusions
                    7. References
                    
                    Format your response in Markdown. Use proper headings, bullet points, and formatting to make the report readable and professional.
                    Be concise but thorough. Include important insights from the research and cite sources where appropriate.
                    """
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_tokens=4000
        )
        
        report = response.choices[0].message.content
        return report
    
    def save_report(self, report: str, run_dir: Path) -> Path:
        """Save the research report to a file"""
        report_path = run_dir / "research_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Research report saved to: {report_path}")
        return report_path
    
    def generate_and_save_report(self, plan: ResearchPlan, search_results: List[SearchResult], run_dir: Path) -> Path:
        """Generate and save a comprehensive research report"""
        report = self.generate_report(plan, search_results)
        report_path = self.save_report(report, run_dir)
        return report_path
