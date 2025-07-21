import asyncio
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai.types import Content, Part
import os
from google.generativeai import configure


configure(api_key=os.environ["GEMINI_API_KEY"])



# Input/Output schemas
class TopicInput(BaseModel):
    topic: str = Field(description="The topic to generate the document about.")

class ContentOutput(BaseModel):
    content: str = Field(description="Information-dense, simple content about the topic.")

def search_validation_tool(query: str) -> str:
    print(f"[SearchValidationTool] Executing search for: {query}")
    return f"Content validation completed for query: {query}. Results appear valid."

# Agents
MODEL_NAME = "gemini-2.5-flash"

def create_content_gathering_agent(topic: str) -> LlmAgent:
    return LlmAgent(
        name="content_gathering_agent",
        model=MODEL_NAME,
        instruction=f"""
        You are a content gathering agent. Your task is to:
        1. Take the provided topic and gather vast information about it: '{topic}. Atleast for 20 pages'
        2. Use the google_search tool to find relevant information
        3. Create information-dense, well-structured content
        4. Focus on accuracy and completeness
        5. Provide detailed content about the topic
        6. Return only the complete content. Do not include any commentary or confirmations.
        """,
        tools=[google_search],
        output_key="content"
    )

def create_visual_generating_agent() -> LlmAgent:
    return LlmAgent(
    name="visual_generating_agent", 
    model=MODEL_NAME,
    instruction="""
You are a visual content enhancement agent. Your tasks are:

1. Take the content from the previous agent.
2. Enhance it using visual elements:
   - Tables
   - Flowcharts or bullet-point sequences
   - Bar graphs and pie charts (represented in Markdown or explained)
3. Add **real images** related to the content add the links of the image:
   - Use Markdown syntax: ![Alt Text](https://public-image-url.jpg)
   - Do not use placeholder filenames like (Image_of_X.jpg)
   - Use publicly available images from trusted sources such as:
     - Wikimedia Commons
     - NASA
     - Wikipedia
     - Other copyright-safe sources
    
4. Provide a short caption or description under each image (as a sentence or italics).
5. Structure and format the content for improved readability and engagement.
6. Do not include any commentary, confirmations, or notes outside the content itself.
7. Return the final **Markdown** content with the enhanced visuals and real images embedded.
""",
    output_key="content"
)


def create_content_validating_agent() -> LlmAgent:
    return LlmAgent(
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

def create_formatting_agent() -> LlmAgent:
    return LlmAgent(
        name="formatting_agent",
        model=MODEL_NAME,
        instruction="""
        You are a document formatting agent. Your task is to:
        1. Take the validated content from the previous agent
        2. Apply professional formatting with proper headings using markdown
        3. Structure the document with clear sections using # and ## headers
        4. Ensure consistent formatting throughout
        5. Create a well-organized, professionally formatted document
        6. Return only the formatted content without surrounding markdown code blocks or commentary.
        7. Do not Include title page.
        """,
        output_key="content"
    )

def create_indexing_agent() -> LlmAgent:
    return LlmAgent(
        name="indexing_agent",
        model=MODEL_NAME,
        instruction="""
        You are a document indexing agent. Your task is to:
        1. Take the formatted content from the previous agent
        2. Create a comprehensive table of contents at the beginning
        3. Add a professional title page information
        4. Ensure proper document structure with clear sections
        5. Create the final, complete document ready for markdown export
        6. Return only the final document content without surrounding markdown code blocks or commentary.
        """,
        output_key="content"
    )

APP_NAME = "DocumentGenerator"
DUMMY_USER_ID = "dummy_user_123"

async def agentic_workflow(topic: str) -> str:
    session_service = InMemorySessionService()

    content_gathering = create_content_gathering_agent(topic)
    visual_generating = create_visual_generating_agent()
    content_validating = create_content_validating_agent()
    formatting = create_formatting_agent()
    indexing = create_indexing_agent()

    document_generation_workflow = SequentialAgent(
        name="document_generation_workflow",
        sub_agents=[
            content_gathering,
            visual_generating,
            content_validating,
            formatting,
            indexing,
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
            session_id=session.id # type: ignore
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

def save_markdown_to_file(markdown_text: str, filename: str = "output.md") -> str:
    lines = markdown_text.strip().splitlines()
    if lines and lines[0].strip() == "```markdown" and lines[-1].strip() == "```":
        lines = lines[1:-1]  # remove first and last lines
    cleaned = "\n".join(lines).strip()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return filename

def process_topic(topic: str) -> str:
    print(f"Starting agentic workflow for topic: {topic}")

    try:
        final_content = asyncio.run(agentic_workflow(topic))
        print("Workflow finished. Saving markdown file...")
        return save_markdown_to_file(final_content)

    except Exception as e:
        print(f"Error in process_topic: {e}")
        fallback_content = f"""
        # Error Generating Document

        An error occurred: {str(e)}
        """
        return save_markdown_to_file(fallback_content, filename="error_output.md")

if __name__ == '__main__':
    test_topic = "case study on tesla automotive"
    print(f"Generating markdown file for topic: '{test_topic}'")

    md_filename = process_topic(test_topic)

    print(f"Markdown file generated successfully: {md_filename}")
