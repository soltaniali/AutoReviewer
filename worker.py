import os
from celery import Celery
import logging
from agents.graph import create_review_graph
from core.workspace import WorkspaceManager
from core.git_manager import GitManager
from core.project_manager import ProjectManager
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
# Use redis://redis:6379/0 if running in docker, otherwise redis://localhost:6379/0
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="worker.run_review_agent")
def run_review_agent(zip_contents: bytes):
    """
    Celery task to execute the multi-agent code review graph.
    It extracts the repo from a zip file, gets the diff, and runs the agent graph.
    If no diff is found, it reviews the entire project content.
    """
    logger.info("Worker received task to run review agent.")
    try:
        # Create a temporary file to write the zip contents to
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            temp_zip.write(zip_contents)
            temp_zip_path = temp_zip.name

        workspace = WorkspaceManager()
        try:
            temp_dir = workspace.load_from_zip(temp_zip_path)
            logger.info(f"Workspace extracted to temporary directory: {temp_dir}")
            
            git_manager = GitManager(repo_path=temp_dir)
            diff = git_manager.get_diff()
            modified_files = git_manager.get_modified_files()

            review_input = ""
            if diff:
                logger.info("Git diff found. Proceeding with diff-based review.")
                review_input = diff
            else:
                logger.warning("No git diff found. Proceeding with full project review.")
                project_manager = ProjectManager(project_path=temp_dir)
                # Create a string representation of all file contexts
                all_context = project_manager.get_all_context()
                review_input = "\n".join(
                    f"--- {path} ---\n{content}" for path, content in all_context.items()
                )

            if not review_input:
                logger.warning("No content to review. Aborting.")
                return "No content found to review in the repository."

            # Initialize and run the agent graph
            graph = create_review_graph()
            
            initial_state = {
                "diff": review_input,
                "repo_path": temp_dir,
                "modified_files": modified_files if modified_files else [],
                "file_contexts": {},
            }
            
            logger.info("Starting graph execution...")
            result = graph.invoke(initial_state)
            
            final_report = result.get("final_review", "Graph executed but no final review was generated.")

            logger.info("Agent graph execution completed.")
            return final_report
        finally:
            workspace.cleanup()
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)


    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", exc_info=True)
        # Re-raise the exception to mark the task as failed in Celery
        raise

