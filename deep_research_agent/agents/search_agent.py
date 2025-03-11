import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

from agents.planner_agent import ResearchStep, ResearchPlan
from utils.file_utils import get_data_dir

class SearchResult(BaseModel):
    """Result of a web search for a research step"""
    step_number: int = Field(..., description="The number of the research step")
    step_instruction: str = Field(..., description="The instruction that was researched")
    search_query: str = Field(..., description="The search query used")
    summary: str = Field(..., description="Summary of the search results")
    citations: List[Dict[str, str]] = Field(default_factory=list, description="Citations from the search")
    raw_response: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict, description="Raw response from the API")

class SearchAgent:
    """Agent responsible for searching the web for information related to research steps"""
    
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.client = OpenAI(api_key=api_key)
            
    def generate_search_query(self, step: ResearchStep) -> str:
        """Generate an effective search query based on the research step"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at crafting effective search queries. 
                    Your task is to convert a research instruction into a concise, specific search query 
                    that will yield the most relevant information. 
                    Format your response as a single search query with no additional text or explanation."""
                },
                {
                    "role": "user",
                    "content": f"Research instruction: {step.instruction}\nExpected outcome: {step.expected_outcome}\n\nCreate a concise search query:"
                }
            ],
            max_tokens=50
        )
        
        search_query = response.choices[0].message.content.strip()
        return search_query
        
    def search_web(self, query: str, user_location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a web search using OpenAI's web search API"""
        tools = [{
            "type": "web_search_preview",
            "search_context_size": "medium"
        }]
        
        if user_location:
            tools[0]["user_location"] = user_location
        
        print(f"Searching for: {query}")
        print(f"Using tools: {tools}")
            
        try:
            print("Calling OpenAI API...")
            response = self.client.responses.create(
                model="gpt-4o",
                tools=tools,
                input=query
            )
            print("Response received from OpenAI API")
            
            print(f"Response type: {type(response)}")
            if hasattr(response, 'model_dump'):
                try:
                    response_dict = response.model_dump()
                    print(f"Response has model_dump method: {list(response_dict.keys())}")
                except Exception as e:
                    print(f"Failed to use model_dump: {e}")

            try:
                print(f"Response dir: {dir(response)[:10]}...")
                print(f"Response has output attribute: {hasattr(response, 'output')}")
                if hasattr(response, 'output'):
                    print(f"Output type: {type(response.output)}")
                    print(f"Output length: {len(response.output) if hasattr(response.output, '__len__') else 'N/A'}")
            except Exception as e:
                print(f"Error inspecting response attributes: {e}")
            
            try:
                search_result = {
                    "model": getattr(response, 'model', 'unknown'),
                    "created_at": getattr(response, 'created_at', None),
                    "output_items": []
                }
                
                if hasattr(response, 'output'):
                    for item in response.output:
                        if hasattr(item, 'model_dump'):
                            item_dict = item.model_dump()
                            search_result["output_items"].append(item_dict)
                        elif isinstance(item, dict):
                            search_result["output_items"].append(item)
                        else:
                            search_result["output_items"].append({"type": str(type(item)), "content": str(item)})
                elif hasattr(response, 'model_dump'):
                    search_result = response.model_dump()
                else:
                    search_result["text"] = str(response)
                
                return search_result
            
            except Exception as e:
                print(f"Error parsing response: {e}")
                return {
                    "error": "Could not parse response", 
                    "error_message": str(e),
                    "response_str": str(response)
                }
                
        except Exception as e:
            print(f"Error searching web: {e}")
            return {"error": str(e)}
            
    def extract_citations(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract citations from the search response"""
        citations = []
        
        try:
            output_items = response.get("output_items", [])
            
            for item in output_items:
                if item.get("type") == "message":
                    contents = item.get("content", [])
                    for content in contents:
                        if content.get("type") == "output_text":
                            annotations = content.get("annotations", [])
                            for annotation in annotations:
                                if annotation.get("type") == "url_citation":
                                    citation = {
                                        "url": annotation.get("url", ""),
                                        "title": annotation.get("title", ""),
                                        "start_index": annotation.get("start_index", 0),
                                        "end_index": annotation.get("end_index", 0)
                                    }
                                    citations.append(citation)
        except Exception as e:
            print(f"Error extracting citations: {e}")
            
        return citations
        
    def extract_summary(self, response: Dict[str, Any]) -> str:
        """Extract the summary text from the search response"""
        summary = ""
        
        try:
            if "output_items" in response:
                output_items = response.get("output_items", [])
                
                for item in output_items:
                    if item.get("type") == "message":
                        contents = item.get("content", [])
                        for content in contents:
                            if content.get("type") == "output_text":
                                text = content.get("text", "")
                                if text:
                                    summary = text
                                    return summary
            
            if not summary and "output_text" in response:
                return response["output_text"]
            
            if not summary and "text" in response:
                return response["text"]
            
            if not summary:
                if "error" in response:
                    summary = f"Error in search: {response.get('error')}"
                    if "error_message" in response:
                        summary += f"\nDetails: {response.get('error_message')}"
                else:
                    summary = f"Summary could not be extracted in a structured way.\nModel: {response.get('model', 'Unknown')}\n"
                    summary += "Please check the raw response for complete information."
        
        except Exception as e:
            print(f"Error extracting summary: {e}")
            summary = f"Error extracting summary: {e}"
            
        return summary
        
    def execute_search_step(self, step: ResearchStep, step_number: int) -> SearchResult:
        """Execute a single research step by searching the web"""
        search_query = self.generate_search_query(step)
        print(f"Generated search query: {search_query}")
        
        search_response = self.search_web(search_query)
        
        summary = self.extract_summary(search_response)
        citations = self.extract_citations(search_response)
        
        if not summary or summary.startswith("Error extracting summary"):
            summary = f"Unable to retrieve results for the search query: '{search_query}'. This could be due to API limitations or connectivity issues. You may want to try refining the search query or checking your internet connection."
        
        search_result = SearchResult(
            step_number=step_number,
            step_instruction=step.instruction,
            search_query=search_query,
            summary=summary,
            citations=citations,
            raw_response=search_response
        )
        
        return search_result
        
    def execute_research_plan(self, plan: ResearchPlan, run_dir: Path) -> List[SearchResult]:
        """Execute the entire research plan by processing each step"""
        search_results = []
        
        search_dir = run_dir / "search_results"
        search_dir.mkdir(exist_ok=True)
        
        for i, step in enumerate(plan.steps, 1):
            print(f"Executing research step {i}/{len(plan.steps)}: {step.instruction[:50]}...")
            
            result = self.execute_search_step(step, i)
            search_results.append(result)
            
            result_path = search_dir / f"step_{i}_result.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
                
            summary_path = search_dir / f"step_{i}_summary.txt"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"RESEARCH STEP {i}: {step.instruction}\n\n")
                f.write(f"SEARCH QUERY: {result.search_query}\n\n")
                f.write(f"SUMMARY:\n{result.summary}\n\n")
                f.write("CITATIONS:\n")
                for citation in result.citations:
                    f.write(f"- {citation.get('title')}: {citation.get('url')}\n")
        
        combined_summary_path = run_dir / "research_summary.txt"
        with open(combined_summary_path, "w", encoding="utf-8") as f:
            f.write(f"RESEARCH SUMMARY FOR: {plan.query}\n\n")
            f.write(f"REASONING: {plan.reasoning}\n\n")
            
            for result in search_results:
                f.write(f"STEP {result.step_number}: {result.step_instruction}\n\n")
                f.write(f"SUMMARY:\n{result.summary}\n\n")
                f.write("---\n\n")
        
        return search_results
