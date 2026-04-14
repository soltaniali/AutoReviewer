import os
import pytest
from unittest.mock import MagicMock

from agents.state import ReviewState
from agents.nodes.planner import run_planner
from agents.nodes.workers import run_bug_detector, run_security_scanner, run_style_checker

@pytest.fixture
def mock_state() -> ReviewState:
    return {
        "repo_path": "/fake/path",
        "diff": "@@ -0,0 +1,5 @@\n+def risky_logic(user_input):\n+    eval(user_input)",
        "modified_files": ["main.py"],
        "file_contexts": {"main.py": "def risky_logic(user_input):\n    eval(user_input)"},
        "required_checks": [],
        "bug_report": None,
        "security_report": None,
        "style_report": None,
        "test_suggestions": None,
        "final_review": None
    }

def test_planner_node(mock_state, monkeypatch):
    """
    Test that the planner correctly categorizes a diff.
    """
    # Mock the LLM to just return a JSON decision
    mock_llm_invoke = MagicMock(return_value=MagicMock(content='{"checks": ["bug", "security"]}'))
    monkeypatch.setattr("agents.nodes.planner.llm_invoke", mock_llm_invoke)
    
    new_state = run_planner(mock_state)
    assert "bug" in new_state["required_checks"]
    assert "security" in new_state["required_checks"]

def test_worker_nodes(mock_state, monkeypatch):
    """
    Test that identical state routed to different workers returns the right report.
    """
    # Bug Detector
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", MagicMock(return_value=MagicMock(content="Bug found: eval() is risky.")))
    state_after_bug = run_bug_detector(mock_state)
    assert state_after_bug["bug_report"] == "Bug found: eval() is risky."
    
    # Security Scanner
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", MagicMock(return_value=MagicMock(content="Security Alert: Remote Code Execution.")))
    state_after_sec = run_security_scanner(mock_state)
    assert state_after_sec["security_report"] == "Security Alert: Remote Code Execution."
    
    # Style Checker
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", MagicMock(return_value=MagicMock(content="Style Issue: Missing docstrings.")))
    state_after_style = run_style_checker(mock_state)
    assert state_after_style["style_report"] == "Style Issue: Missing docstrings."

def test_missing_file_context(mock_state, monkeypatch):
    """
    Test how worker nodes behave when they receive no file context.
    """
    mock_state["file_contexts"] = {}
    mock_state["modified_files"] = []
    
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", MagicMock(return_value=MagicMock(content="No context found.")))
    state_after_bug = run_bug_detector(mock_state)
    assert state_after_bug["bug_report"] == "No context found."

def test_llm_invocation_error(mock_state, monkeypatch):
    """
    Test how the system behaves if an LLM call fails (e.g., network error).
    The node should fail gracefully without crashing.
    """
    def mock_llm_invoke_error(*args, **kwargs):
        raise Exception("Mocked Network Error")
        
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", mock_llm_invoke_error)
    state_after_bug = run_bug_detector(mock_state)
    assert "error" in state_after_bug["bug_report"].lower() or "failed" in state_after_bug["bug_report"].lower()
