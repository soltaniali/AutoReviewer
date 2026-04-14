from typing import TypedDict, List, Dict, Optional

class ReviewState(TypedDict):
    """
    The state shared across all LangGraph nodes during a review cycle.
    """
    repo_path: Optional[str]
    diff: str
    modified_files: List[str]
    file_contexts: Dict[str, str]
    
    # Planner's output (which concurrent checks should run)
    required_checks: List[str]
    
    # Worker reports
    bug_report: Optional[str]
    security_report: Optional[str]
    style_report: Optional[str]
    
    # Sequential report based on Bug Detector
    test_suggestions: Optional[str]
    
    # Final synthesized markdown review
    final_review: Optional[str]
