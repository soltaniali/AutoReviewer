from langgraph.graph import StateGraph, END
from typing import Dict, List, Callable
from agents.state import ReviewState
from agents.nodes.planner import run_planner
from agents.nodes.workers import run_bug_detector, run_security_scanner, run_style_checker
from agents.nodes.synthesizer import run_synthesizer

def route_workers(state: ReviewState) -> List[str]:
    """
    Conditional routing function. Reads what the Planner decided
    and returns a list of subsequent node names to execute in parallel.
    """
    checks = state.get("required_checks", [])
    if not checks:
        return ["synthesizer"]
        
    next_nodes = []
    if "bug" in checks:
        next_nodes.append("bug_detector")
    if "security" in checks:
        next_nodes.append("security_scanner")
    if "style" in checks:
        next_nodes.append("style_checker")
        
    # If the LLM returned weird/invalid checks, default to synthesizer
    if not next_nodes:
        return ["synthesizer"]
        
    return next_nodes

def create_review_graph():
    """
    Builds the LangGraph Multi-Agent execution flow.
    Planner -> [Parallel Workers] -> Synthesizer
    """
    # 1. Initialize State Graph
    workflow = StateGraph(ReviewState)
    
    # 2. Add Nodes
    workflow.add_node("planner", run_planner)
    workflow.add_node("bug_detector", run_bug_detector)
    workflow.add_node("security_scanner", run_security_scanner)
    workflow.add_node("style_checker", run_style_checker)
    workflow.add_node("synthesizer", run_synthesizer)
    
    # 3. Define the Flow
    workflow.set_entry_point("planner")
    
    # After Planner finishes, condition routing decides which parallel paths to take
    workflow.add_conditional_edges(
        "planner", 
        route_workers,
        {
            "bug_detector": "bug_detector",
            "security_scanner": "security_scanner",
            "style_checker": "style_checker",
            "synthesizer": "synthesizer" # Skip straight to end if NO checks needed
        }
    )
    
    # After any parallel worker finishes, flow back into the synthesizer
    workflow.add_edge("bug_detector", "synthesizer")
    workflow.add_edge("security_scanner", "synthesizer")
    workflow.add_edge("style_checker", "synthesizer")
    
    # Finish execution once Synthesizer runs
    workflow.add_edge("synthesizer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app
