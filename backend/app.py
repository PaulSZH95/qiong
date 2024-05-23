import uuid
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from pathlib import Path
import os
from os.path import dirname, join

from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse


from libraries.etl.google_process import DocumentProcess
from libraries.agents.agent import AdvancedGroq
from libraries.agents.agent_tools import *

script_dir = dirname(Path(__file__).absolute())
upload_path = join(script_dir, "data/something.pdf")


current_id = str(uuid.uuid4())
agent_fact = AdvancedGroq(tools=[raq_qa_rerank, raq_qa_hybrid, edgar_report])
agent = agent_fact.agent_create()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
current_id = str(uuid.uuid4())


class Message(BaseModel):
    message: str


@app.get("/chat_point")
async def root(message: Message):
    response = agent.invoke(
        {"input": message.message},
        config={"configurable": {"session_id": current_id}},
    )
    output = response["output"]
    print(output)
    try:
        if len(response["intermediate_steps"]):
            if response["intermediate_steps"][-1][0].tool != "edgar_report":
                ref = response["intermediate_steps"][-1][1].rsplit(": ")[-1]
                output += "\n" + f"references:\n{ref}"
    except:
        pass
    return {"response": output}


@app.post("/fin_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(content={"error": "File must be a PDF"}, status_code=400)

    # Save the uploaded file
    upload_directory = Path(script_dir)
    upload_directory.mkdir(parents=True, exist_ok=True)
    file_path = upload_path

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    response = DocumentProcess.create_rag(upload_path)

    return {"rag_result": response}
