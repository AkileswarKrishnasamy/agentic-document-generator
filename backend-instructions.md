Create a REST API backend application for a Agentic AI document generator using fast api.
Use Google's Agent Development kit as a framework for devloping Agentic Workflow.
[Link-to-Agent-development-kit](https://google.github.io/adk-docs/)
Setup:
    Create a virtual environment for the backend.
    The api key is stored in the system variables as GOOGLE_API_KEY

File Structure:
    Create a file server.py and add all the fastapi code in it 
    Create a file Agent.py and all the Agentic AI code in it 

API Endpoint:
   generate-conent: Gets the text string from the user it should send the data to the agent and should return the data as a pdf.


Agentic workflow

Agent 1: 
Name: Content Gathering Agent
description: Content gatherer to gather all type of content.
Instructions: gather some content about the given topic make the content as simple and information dense use search tool to gather information.
tools: search tool
Model: Gemini 2.5 pro(find the internal name)

once the content is gathered the content is sent to the Agent 2:

Agent 2:
Name: Visual Generating Agent
description: Generates and Add visual data at right place.
Instructions: Analyse the incomming data and generate flowcharts, tables, images and add them at the appropriate place
Model: Gemini 2.5 pro(find the internal name)

once Agent 2 completes it work then the data is sent to the Agent 3


Agent 3:
Name: Conetent Validating Agent
description: Checks the incomming content is valid and not hallicunated.
Instructions: Analyse the incomming data and check if the incomming data is valid and not hallicunated using search tool.
toots: search tool
Model: Gemini 2.5 pro(find the internal name)

once Agent 3 completes it work then the data is sent to Agent 4

Agent 4:
Name: Formatting Agent
description: Formats the incomming data in a professional way.
Instructions: Format the incomming data in professional way use proper heading, font, naming for visual data, justification, spacing, adding page numbers etc.
Model: Gemini 2.5 pro(find the internal name)

once Agent 4 completes it work then the data is sent to Agent 5:

Agent 5:
Name: Indexing Agent
description: Adds index to the document
Instructions: Add frontpage and Index to the document the index should include all the headings and subheading with its page number and a hyperlink to jump to that page when clicked on the heading.
Model: Gemini 2.5 pro(find the internal name)
