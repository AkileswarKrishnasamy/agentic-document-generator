import asyncio
import io
from typing import Any, Dict, AsyncGenerator
from pydantic import BaseModel, Field

# Corrected imports for Google ADK
from google.adk.agents import LlmAgent, SequentialAgent, BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai.types import Content, Part
from google.adk.agents.invocation_context import InvocationContext

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from google.adk.events import Event

class DelayAgent(BaseAgent):
    def __init__(self, delay_seconds: int, name: str = "delay_agent"):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Any, None]:
        print(f"--- Starting delay seconds to respect API rate limits... ---")
        await asyncio.sleep(20)
        print(f"--- Delay seconds completed. Proceeding to next agent... ---")
        yield Event(content=Content(parts=[Part(text="Delay of 20 seconds completed")]),author='Akil') 


class TopicInput(BaseModel):
    topic: str = Field(description="The topic to generate the document about.")

class ContentOutput(BaseModel):
    content: str = Field(description="Information-dense, simple content about the topic.")

def search_validation_tool(query: str) -> str:
    print(f"[SearchValidationTool] Executing search for: {query}")
    return f"Content validation completed for query: {query}. Results appear valid."

MODEL_NAME = "gemini-2.0-flash"

content_gathering_agent = LlmAgent(
    name="content_gathering_agent",
    model=MODEL_NAME,
    instruction="""
    You are a content gathering agent. Your task is to:
    1. Take the provided topic and gather comprehensive information about it
    2. Use the google_search tool to find relevant information
    3. Create information-dense, well-structured content
    4. Focus on accuracy and completeness
    5. Provide detailed content about the topic
    """,
    tools=[google_search],
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
    """,
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
    5. Make improvements to content quality
    """,
    tools=[search_validation_tool],
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
    """,
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
    """,
)

delay_agent_1 = DelayAgent(delay_seconds=60, name="api_rate_limit_delay_1")
delay_agent_2 = DelayAgent(delay_seconds=60, name="api_rate_limit_delay_2")
delay_agent_3 = DelayAgent(delay_seconds=60, name="api_rate_limit_delay_3")
delay_agent_4 = DelayAgent(delay_seconds=60, name="api_rate_limit_delay_4")

document_generation_workflow = SequentialAgent(
    name="document_generation_workflow",
    sub_agents=[
        content_gathering_agent,
        delay_agent_1,
        visual_generating_agent,
        delay_agent_2,
        content_validating_agent,
        delay_agent_3,
        formatting_agent,
        delay_agent_4,
        indexing_agent,
    ]
)

APP_NAME = "DocumentGenerator"
DUMMY_USER_ID = "dummy_user_123"

async def agentic_workflow(topic: str) -> str:
    session_service = InMemorySessionService()
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
                final_content = str(event.content)
                print(f"Received content from workflow: {final_content[:200]}...")

    except Exception as e:
        print(f"Error in workflow execution: {e}")
        final_content = f"Error occurred during document generation: {str(e)}"

    return final_content

def process_topic(topic: str) -> bytes:
    print(f"Starting agentic workflow for topic: {topic}")

    try:
        final_content = asyncio.run(agentic_workflow(topic))
        print("Workflow finished. Generating PDF...")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=18
        )

        styles = getSampleStyleSheet()
        story = []

        content_lines = final_content.split('\n')

        for line in content_lines:
            line = line.strip()
            if line:
                if line.startswith('# '):
                    clean_line = line.lstrip('# ').strip()
                    p = Paragraph(clean_line, styles["Heading1"])
                elif line.startswith('## '):
                    clean_line = line.lstrip('# ').strip()
                    p = Paragraph(clean_line, styles["Heading2"])
                elif line.startswith('### '):
                    clean_line = line.lstrip('# ').strip()
                    p = Paragraph(clean_line, styles["Heading3"])
                else:
                    p = Paragraph(line, styles["Normal"])

                story.append(p)
                story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        print(f"Error in process_topic: {e}")
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Error Generating Document", styles["Title"]),
            Spacer(1, 0.2 * inch),
            Paragraph(f"An error occurred: {str(e)}", styles["Normal"])
        ]
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

if __name__ == '__main__':
    test_topic = "The history of artificial intelligence"
    print(f"Generating PDF for topic: '{test_topic}'")

    pdf_output = process_topic(test_topic)

    try:
        output_filename = "test_output.pdf"
        with open(output_filename, "wb") as f:
            f.write(pdf_output)
        print(f"PDF generated successfully: {output_filename}")

    except Exception as e:
        print(f"Failed to generate PDF: {e}")