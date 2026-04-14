# Project: Production-Grade Multi-Agent Code Review System

## Core Concept
A highly asynchronous, multi-agent code review system that processes PRs via external APIs, coordinates specialized agents to analyze code, filters out noise, and allows developers to chat with the PR context. This project demonstrates enterprise-level engineering practices (observability, async queues, ML evaluation, custom proxy routing).

## Technical Architecture

### 1. AI Gateway & Inference Proxy
- **Tool:** MLflow Deployments Server (AI Gateway)
- **Function:** Proxies LLM calls, securely holds API keys from third-party AI providers, defines rate limits, handles retries, and standardizes the API format. Uses a custom `base_url` for flexibility (OpenAI, Anthropic, OpenRouter, Azure, local vLLM).

### 2. Webhook & Task Queuing
- **Tools:** FastAPI, Redis, Celery
- **Function:** FastAPI receives GitHub PR webhooks and immediately returns 200 OK to prevent timeouts. The webhook payload is pushed to a Redis message queue where background Celery workers pick it up for async processing. Ready to scale via Kubernetes (K8s) for high load (e.g., 100+ PRs/day).

### 3. Context Retrieval Engine (RAG/AST)
- **Function:** Extracts raw Git diffs from PR webhooks. Fetches the *surrounding, unmodified code* using AST parsing or a lightweight vector store to provide deep context and prevent hallucinations (e.g., understanding how a changed function is used elsewhere). Optimizes token limits by chunking large files.

### 4. Multi-Agent Orchestration
- **Tool:** LangGraph
- **Agents:**
  - **The Planner (LLM-based):** Categorizes the PR based on diff/description to determine which sub-agents to trigger.
  - **Bug Detector (Parallel):** Identifies logical errors and edge cases.
  - **Security Scanner (Parallel):** Checks for OWASP vulnerabilities and hardcoded secrets.
  - **Style/Architecture Checker (Parallel):** Verifies alignment with project conventions.
  - **Test Suggester (Sequential):** Uses Bug Detector output to write targeted regression tests.
  - **Synthesizer / Lead Developer (LLM-based):** Reviews sub-agent outputs, filters noise/hallucinations, groups comments, and formats the final GitHub review.

### 5. Observability & Monitoring
- **Tool:** LangSmith
- **Function:** Real-time tracing of LangGraph executions. Tracks token usage, latency per component, cost, and allows deep debugging of individual node steps and agent reasoning.

### 6. Offline Prompt Engineering & Evaluation
- **Tool:** MLflow (Tracking & LLM Evaluate)
- **Function:** Tracks "LLM experiments" (prompt updates, model parameter tweaks). Uses `mlflow.evaluate()` (LLM-as-a-judge) in a CI/CD pipeline against a dataset of historical, merged PRs to quantitatively score new agent versions before deployment.

### 7. User Interface
- **Tool:** Chainlit
- **Function:** A chat interface where developers can paste a PR link, load the LangGraph state, and ask interactive questions (e.g., "Why flag this security issue?" or "Write the fix for me").

## Implementation Phases
1. **Foundation & Gateway:** Setup Python environment, configure MLflow Deployments Server, FastAPI webhook receiver, and Redis/Celery basics.
2. **Context & Evaluators:** Build GitHub diff/context extractor. Setup MLflow evaluation script using a small test fixture.
3. **The Multi-Agent Graph:** Implement LangGraph nodes (Planner, Bug Detector, etc.), wire them up, and inject LangSmith tracing.
4. **Integration:** Connect FastAPI -> Celery -> LangGraph. Implement the Synthesizer to output final reviews.
5. **UI & Polish:** Build Chainlit app for Q&A. Complete >80% test coverage using pytest/pytest-mock.
6. **Infrastructure:** Dockerize all services (`docker-compose.yml`) and optionally create K8s manifests.