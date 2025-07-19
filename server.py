from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from Agent import process_topic
import io

app = FastAPI()

@app.post("/generate-content")
def generate_content(topic: str = Form(...)):
    # Process the topic through the agentic workflow
    pdf_bytes = process_topic(topic)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=generated_document.pdf"}) 