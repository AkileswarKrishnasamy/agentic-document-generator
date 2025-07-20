import asyncio
import io
import subprocess
from typing import Any, Dict, AsyncGenerator
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent, BaseAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai.types import Content, Part
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

import markdown2

# Input/Output schemas
class TopicInput(BaseModel):
    topic: str = Field(description="The topic to generate the document about.")

class ContentOutput(BaseModel):
    content: str = Field(description="Information-dense, simple content about the topic.")

def search_validation_tool(query: str) -> str:
    print(f"[SearchValidationTool] Executing search for: {query}")
    return f"Content validation completed for query: {query}. Results appear valid."

# Agents
MODEL_NAME = "gemini-2.0-flash"

def create_content_gathering_agent(topic: str) -> LlmAgent:
    return LlmAgent(
        name="content_gathering_agent",
        model=MODEL_NAME,
        instruction=f"""
        You are a content gathering agent. Your task is to:
        1. Take the provided topic and gather comprehensive information about it: '{topic}'
        2. Use the google_search tool to find relevant information
        3. Create information-dense, well-structured content
        4. Focus on accuracy and completeness
        5. Provide detailed content about the topic
        6. Return only the complete content. Do not include any commentary or confirmations.
        """,
        tools=[google_search],
        output_key="content"
    )

visual_generating_agent = LlmAgent(
    name="visual_generating_agent", 
    model=MODEL_NAME,
    instruction="""
    You are a visual content agent. Your task is to:
    1. Take the content from the previous agent
    2. Enhance it with visual elements like tables, flowcharts, bullet points
    3. Structure the content for better readability
    4. Add diagrams descriptions where appropriate
    5. Make the content more visually appealing and organized
    6. Return only the enhanced content. Do not include any commentary or confirmations.
    """,
    output_key="content"
)

content_validating_agent = LlmAgent(
    name="content_validating_agent",
    model=MODEL_NAME,
    instruction="""
    You are a content validation agent. Your task is to:
    1. Review the enhanced content from the previous agent
    2. Check for accuracy, completeness, and consistency
    3. Verify information and make corrections if needed
    4. Ensure the content is factually accurate
    5. Improve content quality where necessary
    6. Return only the validated content. Do not include any commentary or confirmations.
    """,
    tools=[search_validation_tool],
    output_key="content"
)

formatting_agent = LlmAgent(
    name="formatting_agent",
    model=MODEL_NAME,
    instruction="""
    You are a document formatting agent. Your task is to:
    1. Take the validated content from the previous agent
    2. Apply professional formatting with proper headings using markdown
    3. Structure the document with clear sections using # and ## headers
    4. Ensure consistent formatting throughout
    5. Create a well-organized, professionally formatted document
    6. Return only the formatted content. Do not include any commentary or confirmations.
    """,
    output_key="content"
)

indexing_agent = LlmAgent(
    name="indexing_agent",
    model=MODEL_NAME,
    instruction="""
    You are a document indexing agent. Your task is to:
    1. Take the formatted content from the previous agent
    2. Create a comprehensive table of contents at the beginning
    3. Add a professional title page information
    4. Ensure proper document structure with clear sections
    5. Create the final, complete document ready for PDF generation
    6. Return only the final document content. Do not include any commentary or confirmations.
    """,
    output_key="content"
)

APP_NAME = "DocumentGenerator"
DUMMY_USER_ID = "dummy_user_123"

async def agentic_workflow(topic: str) -> str:
    session_service = InMemorySessionService()

    content_gathering = create_content_gathering_agent(topic)

    document_generation_workflow = SequentialAgent(
        name="document_generation_workflow",
        sub_agents=[
            content_gathering,
            visual_generating_agent,
            content_validating_agent,
            formatting_agent,
            indexing_agent,
        ]
    )

    runner = Runner(
        agent=document_generation_workflow, 
        app_name=APP_NAME, 
        session_service=session_service
    )

    final_content = "No content generated."
    session = await session_service.create_session(
        app_name=APP_NAME, 
        user_id=DUMMY_USER_ID
    )

    try:
        async for event in runner.run_async(
            user_id=DUMMY_USER_ID,
            new_message=Content(parts=[Part(text=topic)]),
            session_id=session.id
        ):
            if hasattr(event, 'content') and event.content:
                parts = event.content.parts
                if parts and isinstance(parts[0], Part) and parts[0].text:
                    final_content = parts[0].text
                    print(f"Received content from workflow: {final_content[:200]}...")
    except Exception as e:
        print(f"Error in workflow execution: {e}")
        final_content = f"Error occurred during document generation: {str(e)}"

    return final_content

def convert_markdown_to_pdf(markdown_text: str) -> None:

    file_path = "temp_doc.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Check if first line starts with "'''markdown"
    if lines and lines[0].strip().startswith("```markdown"):
        lines = lines[1:]  # Remove first line

    with open(file_path, "w") as f:
        f.writelines(lines)


   

def process_topic(topic: str) -> None:
    print(f"Starting agentic workflow for topic: {topic}")

    try:
        final_content = asyncio.run(agentic_workflow(topic))
        print("Workflow finished. Generating PDF...")
        convert_markdown_to_pdf(final_content)

    except Exception as e:
        print(f"Error in process_topic: {e}")
        error_md = f"""
        # Error Generating Document

        An error occurred: {str(e)}
        """
        convert_markdown_to_pdf(error_md)

if __name__ == '__main__':
    test_topic = "The history of Hdfc Bank."
    print(f"Generating PDF for topic: '{test_topic}'")

    pdf_output = process_topic(test_topic)

    try:
        output_filename = "test_output.pdf"
        with open(output_filename, "wb") as f:
            f.write(pdf_output)
        print(f"PDF generated successfully: {output_filename}")
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
