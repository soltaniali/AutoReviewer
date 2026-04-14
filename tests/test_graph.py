import pytest
from unittest.mock import MagicMock

from agents.state import ReviewState
from agents.graph import create_review_graph

def test_synthesizer_output(monkeypatch):
    """
    Test the Synthesizer node directly to ensure it safely aggregates reports.
    """
    from agents.nodes.synthesizer import run_synthesizer
    
    mock_state: ReviewState = {
        "repo_path": "/fake/path",
        "diff": "@@ -0,0 +1,1 @@\n+x=1",
        "modified_files": [],
        "file_contexts": {},
        "required_checks": ["bug", "security", "style"],
        "bug_report": "Bug: x is unused.",
        "security_report": "Security: looks safe.",
        "style_report": "Style: perfectly formatted.",
        "test_suggestions": None,
        "final_review": None
    }
    
    mock_llm_invoke = MagicMock(return_value=MagicMock(content="### Final Review\n- Bug: x unused\n- Security: safe\n- Style: perfect"))
    monkeypatch.setattr("agents.nodes.synthesizer.llm_invoke", mock_llm_invoke)
    
    new_state = run_synthesizer(mock_state)
    assert "### Final Review" in new_state["final_review"]
    
    # Ensure it passed the individual reports to the LLM
    call_args = mock_llm_invoke.call_args[0][0]
    assert "Bug: x is unused." in call_args
    assert "Security: looks safe." in call_args


def test_graph_compilation_and_execution(monkeypatch):
    """
    Test that the LangGraph compiles and successfully executes end-to-end.
    """
    # Mock LLM across all nodes to prevent real API calls
    mock_llm = MagicMock(return_value=MagicMock(content="Mocked LLM Response"))
    
    # Planner needs valid JSON
    mock_planner_llm = MagicMock(return_value=MagicMock(content='{"checks": ["bug", "security"]}'))
    monkeypatch.setattr("agents.nodes.planner.llm_invoke", mock_planner_llm)
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", mock_llm)
    monkeypatch.setattr("agents.nodes.synthesizer.llm_invoke", mock_llm)
    
    graph = create_review_graph()
    
    input_state = {
        "diff": "@@ -1 +1 @@\n- old\n+ new",
        "modified_files": ["main.py"],
        "file_contexts": {"main.py": "new code"},
    }
    
    # Run the graph
    result_state = graph.invoke(input_state)
    
    # Planner should have mandated bug and security
    assert result_state["required_checks"] == ["bug", "security"]
    
    # Workers should have attached their reports
    assert result_state["bug_report"] == "Mocked LLM Response"
    assert result_state["security_report"] == "Mocked LLM Response"
    
    # Style checker was NOT requested by planner, should be None
    assert result_state.get("style_report") is None
    
    # Synthesizer should have ran and populated final_review
    assert result_state["final_review"] == "Mocked LLM Response"

def test_planner_empty_checks(monkeypatch):
    """
    Test scenario where the planner node returns an empty list of checks.
    """
    mock_llm = MagicMock(return_value=MagicMock(content="Mocked LLM Response"))
    mock_planner_llm = MagicMock(return_value=MagicMock(content='{"checks": []}'))
    
    monkeypatch.setattr("agents.nodes.planner.llm_invoke", mock_planner_llm)
    monkeypatch.setattr("agents.nodes.workers.llm_invoke", mock_llm)
    monkeypatch.setattr("agents.nodes.synthesizer.llm_invoke", mock_llm)
    
    graph = create_review_graph()
    
    input_state = {
        "diff": "@@ -1 +1 @@\n- old\n+ new",
        "modified_files": ["main.py"],
        "file_contexts": {"main.py": "new code"},
    }
    
    result_state = graph.invoke(input_state)
    
    assert result_state["required_checks"] == []
    # If no required checks, workers shouldn't have been called
    assert result_state.get("bug_report") is None
    assert result_state.get("security_report") is None
    assert result_state.get("style_report") is None

def test_synthesizer_empty_reports(monkeypatch):
    """
    Test the synthesizer node's behavior when one or more of the worker reports are empty or None.
    """
    from agents.nodes.synthesizer import run_synthesizer
    
    mock_state: ReviewState = {
        "repo_path": "/fake/path",
        "diff": "diff content",
        "modified_files": [],
        "file_contexts": {},
        "required_checks": ["bug", "security"],
        "bug_report": None,
        "security_report": "",
        "style_report": None,
        "test_suggestions": None,
        "final_review": None
    }
    
    mock_llm_invoke = MagicMock(return_value=MagicMock(content="Review with empty reports"))
    monkeypatch.setattr("agents.nodes.synthesizer.llm_invoke", mock_llm_invoke)
    
    new_state = run_synthesizer(mock_state)
    assert new_state["final_review"] == "No issues found by any agents. Looks good to merge!"
    mock_llm_invoke.assert_not_called()
