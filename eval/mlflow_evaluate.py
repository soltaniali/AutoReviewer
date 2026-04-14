import os
import sys
import pandas as pd
import mlflow
from typing import Dict, Any

# Ensure local imports work correctly for execution
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agents.graph import create_review_graph

def dummy_predict(inputs: pd.DataFrame) -> list[str]:
    """
    Mock prediction wrapper for mlflow.evaluate.
    Accepts dataframe of diffs as inputs, returns list of review texts.
    """
    graph = create_review_graph()
    results = []
    
    for _, row in inputs.iterrows():
        try:
            initial_state = {
                "diff": row["diff_text"],
                "repo_path": "/mock/path/to/repo",
                "modified_files": [],
                "file_contexts": {}
            }
            # Execute agent graph (using sync invoke)
            result = graph.invoke(initial_state)
            final_report = result.get("final_review", "Execution failed")
            results.append(final_report)
        except Exception as e:
            results.append(f"Error during graph execution: {e}")
            
    return results

def run_evaluation():
    """
    Sets up an MLflow evaluation testing the LLM multi-agent review graph
    against a small fixture of diffs.
    """
    # 1. Configure MLflow experiment tracking
    mlflow.set_tracking_uri("sqlite:///mlflow.db") # For local lightweight execution, change to deployed tracking server if needed.
    mlflow.set_experiment("Code_Review_Agent_Eval")

    # 2. Define a small 'golden dataset' (test fixture)
    dataset = pd.DataFrame({
        "diff_text": [
            "@@ -0,0 +1,5 @@\n+def divide(a, b):\n+    return a / b\n+def add(a, b):\n+    return a + b",
            "@@ -10,2 +10,2 @@\n- API_KEY = os.environ.get('API_KEY')\n+ API_KEY = 'sk-1234567890abcdef' \n+ client = Client(api_key=API_KEY)",
        ],
        "expected_review": [
            "Missing check for ZeroDivisionError in `divide` function.",
            "Hardcoded API_KEY secret detected. Never commit secrets directly to code."
        ]
    })

    eval_data = mlflow.data.from_pandas(
        dataset,
        predictions=None,
        targets="expected_review",
    )

    print("Starting MLflow evaluation for agent performance...")
    
    with mlflow.start_run(run_name="agent-eval-v1"):
        eval_result = mlflow.evaluate(
            model=dummy_predict,
            data=eval_data,
            model_type="text-summarization",
            extra_metrics=[
                # You can add custom heuristic metrics here, like keyword presence matching
            ],
            evaluators=["default"] 
        )
        
        print("\nEvaluation Results:")
        print(eval_result.metrics)
        print("\nReview Sample Outputs:")
        for idx, res in enumerate(eval_result.predictions):
            print(f"Prediction {idx+1}:\n{res}\n")

if __name__ == "__main__":
    run_evaluation()
