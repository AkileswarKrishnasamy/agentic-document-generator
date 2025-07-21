from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
from Agent import process_topic
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-content")
def generate_content(topic: str = Form(...)):
    # Run the agentic workflow and generate the markdown file
    markdown_path = process_topic(topic)

    # Open the markdown file and return it as a response
    with open(markdown_path, "rb") as f:
        return StreamingResponse(
            io.BytesIO(f.read()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={markdown_path}"}
        )
