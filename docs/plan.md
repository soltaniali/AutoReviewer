# Actionable Implementation Plan & To-Do List

**Project: Production-Grade Multi-Agent Code Review System (Local Repo Execution)**

This plan is tailored for a system that receives a local repository directory path on your computer, evaluates the uncommitted changes (or a specific branch/commit diff), runs the multi-agent graph, and provides an enterprise-grade review locally.

## Phase 1: Foundation & Gateway Infrastructure
- [ ] Initialize Python project (e.g., `poetry init` or `requirements.txt`).
- [ ] Install core dependencies: `fastapi`, `uvicorn`, `gitpython`, `langchain`, `langgraph`, `mlflow`, `litellm`, `chainlit`.
- [ ] Set up the directory structure (`cli/`, `api/`, `core/`, `agents/`, `ui/`).
- [ ] Create `docker-compose.yml` to spin up the local Data ecosystem (Redis, PostgreSQL for MLflow tracking, MLflow AI Gateway).
- [ ] Configure `gateway/config.yaml` to point to the third-party AI provider using your custom `base_url`.
- [ ] Start the MLflow AI Gateway and verify local connectivity.

## Phase 2: Local Git Context Retrieval Engine 
- [ ] Write `core/git_manager.py` using `GitPython` or `subprocess`.
  - [ ] Implement a function to extract the local `git diff` (either uncommitted changes or diff against `main`).
  - [ ] Implement local file reading: given a diff, read the entire surrounding file directly from the local disk.
  - [ ] Implement simple AST parsing/chunking on the local files to extract dependencies for deeper context.
- [ ] Write the CLI entry point (`cli/main.py`) or local FastAPI route that accepts `--repo-path="e:/work/my-project"`.

## Phase 3: The LangGraph Multi-Agent Core
- [ ] Define the LangGraph State (`agents/graph.py`) to hold: `repo_path`, `diff_content`, `file_contexts`, and `review_comments`.
- [ ] Build the **Planner Agent**: Evaluates the local diff to decide which checks are needed.
- [ ] Build the Parallel Worker Nodes: 
  - [ ] **Bug Detector**: Analyzes logic.
  - [ ] **Security Scanner**: Analyzes for local vulnerabilities/secrets.
  - [ ] **Style Checker**: Checks styling.
- [ ] Build the **Test Suggester** node (runs sequentially after Bug Detector).
- [ ] Build the **Synthesizer (Lead Developer)** node to format the final Markdown output.
- [ ] Wire the nodes together into the LangGraph workflow.
- [ ] Configure local LangSmith environment variables (`LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2=true`).

## Phase 4: Local Output & MLflow Evaluation
- [ ] Hook the CLI/API trigger to execute the LangGraph workflow synchronously (or return an async job ID).
- [ ] Have the Synthesizer output the review locally (e.g., generate a `review_report.md` in the target repo's directory or print beautifully to the terminal).
- [ ] Set up `eval/mlflow_evaluate.py`. 
  - [ ] Define a "golden dataset" of local mock diffs and expected review points.
  - [ ] Write a script using `mlflow.evaluate()` (LLM-as-a-judge) to test the agent system and log performance.

## Phase 5: Chainlit UI & Interactive Debugging
- [ ] Build `ui/app.py` using Chainlit. 
- [ ] Create an interface where a user can input their local repo path (e.g., `E:\work\portfolio1`).
- [ ] The Chainlit app triggers the agent workflow, displays the final review, and allows the developer to chat with the agents based on their local code context ("Why did you flag line 42 in my local file?").
- [ ] Write comprehensive unit tests for the Git extraction and LangGraph routing logic (>80% coverage).