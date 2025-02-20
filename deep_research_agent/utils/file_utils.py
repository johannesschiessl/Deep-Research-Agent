from datetime import datetime
import json
import random
import string
from pathlib import Path
from typing import Any

def get_data_dir() -> Path:
    """Get the base data directory path"""
    base_dir = Path("data")
    base_dir.mkdir(exist_ok=True)
    return base_dir

def generate_run_id(length: int = 8) -> str:
    """Generate a simple random run ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_run_directory() -> tuple[Path, str]:
    """Create a new run directory with today's date and a unique run ID"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    run_id = generate_run_id()
    
    date_dir = get_data_dir() / date_str
    date_dir.mkdir(exist_ok=True)
    
    run_dir = date_dir / run_id
    run_dir.mkdir(exist_ok=True)
    
    return run_dir, run_id

def save_plan_to_json(plan: Any, run_dir: Path) -> Path:
    """Save a plan to plan.json in the specified run directory"""
    plan_path = run_dir / "plan.json"
    
    if hasattr(plan, "model_dump"):
        plan_dict = plan.model_dump()
    else:
        plan_dict = plan
        
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, indent=2, ensure_ascii=False)
        
    return plan_path