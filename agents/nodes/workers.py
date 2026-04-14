from typing import Dict, Any

from agents.state import ReviewState

def llm_invoke(prompt: str) -> Any:
    # We will share this utility or extract it to an `llm_manager.py` later.
    from agents.nodes.planner import llm_invoke as _llm
    return _llm(prompt)

def run_bug_detector(state: ReviewState) -> dict:
    """ Identifies logical errors and edge cases. """
    context = ""
    for f, content in state.get("file_contexts", {}).items():
        context += f"\n--- {f} ---\n{content}\n"
    
    diff = state.get("diff", "")
    
    prompt = (
        "You are an expert software engineer reviewing a Pull Request. "
        "Your focus is ONLY on identifying logical bugs, edge cases, and runtime exceptions. "
        f"Do not comment on style or formatting.\n\nContext:\n{context}\n\nDiff:\n{diff}"
    )
    
    try:
        msg = llm_invoke(prompt)
        return {"bug_report": msg.content}
    except Exception as e:
        return {"bug_report": f"Error executing Bug Detector: {str(e)}"}

def run_security_scanner(state: ReviewState) -> dict:
    """ Checks for OWASP vulnerabilities and hardcoded secrets. """
    context = ""
    for f, content in state.get("file_contexts", {}).items():
        context += f"\n--- {f} ---\n{content}\n"
    
    diff = state.get("diff", "")
    
    prompt = (
        "You are an expert Security Engineer. "
        "Review the following code changes for security vulnerabilities (e.g. injection, XSS, exposed secrets). "
        f"If no vulnerabilities are found, output 'No security issues found'.\n\nContext:\n{context}\n\nDiff:\n{diff}"
    )
    
    try:
        msg = llm_invoke(prompt)
        return {"security_report": msg.content}
    except Exception as e:
        return {"security_report": f"Error executing Security Scanner: {str(e)}"}

def run_style_checker(state: ReviewState) -> dict:
    """ Verifies alignment with project conventions. """
    diff = state.get("diff", "")
    
    prompt = (
        "You are a Style Guide Enforcer. "
        "Review the following diff for violations of PEP8 (if Python) or general poor naming/formatting conventions. "
        f"Be very concise.\n\nDiff:\n{diff}"
    )
    
    try:
        msg = llm_invoke(prompt)
        return {"style_report": msg.content}
    except Exception as e:
        return {"style_report": f"Error executing Style Checker: {str(e)}"}
