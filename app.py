import chainlit as cl
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from core.workspace import WorkspaceManager
from core.project_manager import ProjectManager
from agents.graph import create_review_graph

load_dotenv()

@cl.on_chat_start
async def on_chat_start():
    # Store the graph app in user session
    app = create_review_graph()
    cl.user_session.set("graph", app)
    cl.user_session.set("current_report", None)
    
    welcome_msg = """# 🔍 Multi-Agent Code Review System

I analyze your code across multiple dimensions:

• 🐛 Bug Detection - Logic errors and potential runtime issues
• 🔐 Security Analysis - Vulnerabilities and unsafe patterns
• 💄 Code Style - Best practices and maintainability
• 🧪 Test Coverage - Testing recommendations

## How to use:
1. Upload a .zip file of your repository
2. I'll extract and analyze your code
3. Ask follow-up questions about the report

## Example questions after review:
- "Explain the bug in main.py"
- "How do I fix the security issue?"
- "What are the style improvements?"
"""
    
    await cl.Message(content=welcome_msg).send()

@cl.on_message
async def main(message: cl.Message):
    graph = cl.user_session.get("graph")
    current_report = cl.user_session.get("current_report")
    
    # Check if this is a file upload
    if message.elements:
        zip_file = [file for file in message.elements if file.name.endswith(".zip")]
        
        if not zip_file:
            await cl.Message(content="📦 I only accept .zip files. Please upload your project in ZIP format.").send()
            return
            
        file = zip_file[0]
        
        # Process the zip file
        with WorkspaceManager() as workspace:
            extract_dir = workspace.load_from_zip(file.path)
            
            # Load project context
            pm = ProjectManager(extract_dir)
            context = pm.get_all_context()
            
            if not context["modified_files"]:
                await cl.Message(content="⚠️ The ZIP file appears to be empty or contains no readable code files.").send()
                return
                
            file_count = len(context["modified_files"])
            
            # For zip uploads, we might not have a formal diff, so let's combine file contexts
            # Limit to 5 files to avoid exceeding the LLM context window natively
            safe_contexts = dict(list(context["file_contexts"].items())[:5])
            combined_code = "\n".join([f"--- {f} ---\n{c}" for f, c in safe_contexts.items()])
            
            # Build initial state
            initial_state = {
                "repo_path": extract_dir,
                "diff": f"Reviewing codebase upload:\n{combined_code}",
                "modified_files": context["modified_files"][:5],
                "file_contexts": safe_contexts,
                "required_checks": [],
                "bug_report": None,
                "security_report": None,
                "style_report": None,
                "test_suggestions": None,
                "final_review": None
            }
            
            # Use Chainlit Steps for progress tracking
            agent_configs = {
                "planner": {"name": "🤖 Planner", "description": "Planning review scope"},
                "bug_detector": {"name": "🐛 Bug Detector", "description": "Detecting logic errors"},
                "security_scanner": {"name": "🔐 Security Analyzer", "description": "Finding vulnerabilities"},
                "style_checker": {"name": "💄 Style Checker", "description": "Checking code quality"},
                "synthesizer": {"name": "📝 Synthesizer", "description": "Compiling final report"}
            }
            
            # Wrap the streaming in async context
            def stream_graph():
                return list(graph.stream(initial_state))
            
            events_list = await cl.make_async(stream_graph)()
            
            final_state = initial_state
            
            # Show each agent's progress step-by-step
            for event in events_list:
                # Events are in format {node_name: state_dict}
                for node_name, state_update in event.items():
                    if node_name in agent_configs:
                        config = agent_configs[node_name]
                        
                        # Send agent started message
                        progress = f"⏳ **{config['name']}** - Processing..."
                        await cl.Message(content=progress).send()
                        
                        # Extract relevant output from state
                        output_lines = []
                        
                        if node_name == "planner" and "required_checks" in state_update:
                            checks = state_update.get("required_checks", [])
                            checks_text = ', '.join(checks) if checks else 'none'
                            output_lines.append(f"Planned checks: {checks_text}")
                        
                        elif node_name == "bug_detector" and "bug_report" in state_update:
                            report = state_update.get("bug_report")
                            if report:
                                output_lines.append(report)
                        
                        elif node_name == "security_scanner" and "security_report" in state_update:
                            report = state_update.get("security_report")
                            if report:
                                output_lines.append(report)
                        
                        elif node_name == "style_checker" and "style_report" in state_update:
                            report = state_update.get("style_report")
                            if report:
                                output_lines.append(report)
                        
                        # Send completion with details
                        if output_lines:
                            details = "\n\n".join(output_lines)
                            completion = f"✅ **{config['name']}** - Complete\n\n{details}"
                            await cl.Message(content=completion).send()
                        
                        final_state = state_update
            
            final_review = final_state.get("final_review", "No review could be generated.")
            
            # Store the report in session for follow-up questions
            cl.user_session.set("current_report", final_review)
            
            # Send final report - clean plain content
            final_msg = f"""# ✅ FINAL CODE REVIEW

{final_review}"""
            
            await cl.Message(content=final_msg).send()
            
            # Add followup prompt
            await cl.Message(content="💬 Feel free to ask follow-up questions about this report!").send()
    
    else:
        # Handle text messages (follow-up questions about the report)
        if not current_report:
            await cl.Message(content="📝 Please upload a .zip file first to generate a code review report.").send()
            return
        
        # User is asking a follow-up question
        user_question = message.content
        
        # Use the LLM to answer questions about the report
        from litellm import completion
        
        qa_prompt = f"""You are a code review assistant. A user has received a code review report and has a follow-up question about it.

ORIGINAL REPORT:
{current_report}

USER QUESTION:
{user_question}

Provide a helpful, concise answer based on the report above."""
        
        try:
            base_url = os.environ.get("OPENAI_API_BASE", "https://api.metisai.ir/openai/v1")
            api_key = os.environ.get("OPENAI_API_KEY")
            
            response = completion(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": qa_prompt}],
                api_base=base_url,
                api_key=api_key,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            await cl.Message(content=f"📌 {answer}").send()
        
        except Exception as e:
            await cl.Message(content=f"❌ Error processing your question: {str(e)}").send()
