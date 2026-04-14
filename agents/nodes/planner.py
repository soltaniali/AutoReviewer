import json
import logging
from typing import Dict, Any

from agents.state import ReviewState

logger = logging.getLogger(__name__)

def llm_invoke(prompt: str) -> Any:
    """
    Wrapper around Litellm/Langchain invocation.
    This will be configured to route to MLflow Deployments later.
    For now, placeholder to allow mocking.
    """
    # Import locally to avoid slow initializations
    from litellm import completion
    import os
    from dotenv import load_dotenv
    
    # Load local .env if present
    load_dotenv()
    
    # In production (Docker), this will be injected. 
    # For local testing, we default to the local MLflow Gateway.
    base_url = os.environ.get("OPENAI_API_BASE", "http://localhost:5000/gateway/test-chat/invocations")
    
    try:
        kwargs = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        }
        if os.environ.get("OPENAI_API_BASE"):
            kwargs["api_base"] = os.environ.get("OPENAI_API_BASE")
        if os.environ.get("OPENAI_API_KEY"):
            kwargs["api_key"] = os.environ.get("OPENAI_API_KEY")
        elif os.environ.get("GATEWAY_TOKEN"):
            kwargs["api_key"] = os.environ.get("GATEWAY_TOKEN")

        response = completion(**kwargs)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        class DummyMsg:
            content = "{}"
        return DummyMsg()

def run_planner(state: ReviewState) -> ReviewState:
    """
    Determines which expert agents to run based on the diff and context.
    """
    diff = state.get("diff", "")
    
    prompt = (
        f"Analyze the following code diff and determine which checks are necessary.\n"
        f"Respond ONLY with a JSON object in this format: {{\"checks\": [\"bug\", \"security\", \"style\"]}}.\n"
        f"Options: 'bug' (logic changes), 'security' (potential vulnerabilities), 'style' (formatting/linting).\n\n"
        f"Diff:\n{diff}"
    )
    
    msg = llm_invoke(prompt)
    try:
        decision = json.loads(msg.content)
        checks = decision.get("checks", ["bug", "security", "style"])
    except json.JSONDecodeError:
        # Fallback to running all if parsing fails
        checks = ["bug", "security", "style"]
        
    # Return delta for LangGraph State
    return {"required_checks": checks}
