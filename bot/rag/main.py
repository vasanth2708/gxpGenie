from fastapi import FastAPI, HTTPException
import json
import asyncio
from prompts.prompt import URS_prompt, FRS_prompt
from combined import create_rag_model,model_call
from magnum import Magnum

app = FastAPI()#
handler = Magnum(app)    

@app.get("/urs_report")
async def urs_reporter():
    urs_path = "gxpgenie"
    urs_vectorstore = await create_rag_model(urs_path,"reports/Sample_URS.pdf")
    urs_report = await model_call(urs_vectorstore, URS_prompt(), "Generate Detailed Report Analysis")
    response = {
        "urs" : urs_report
    }
    return response


@app.get("/full_report")
async def frs_reporter():
    urs_path = "gxpgenie"
    urs_vectorstore = await create_rag_model(urs_path,"reports/Sample_URS.pdf")
    urs_report = await model_call(urs_vectorstore, URS_prompt(), "Generate Detailed Report Analysis")
    frs_path = "gxpgenie"
    frs_vectorstore = await create_rag_model(frs_path,"reports/Sample_URS.pdf")
    frs_report = await model_call(frs_vectorstore, FRS_prompt(), "Generate Detailed Report Analysis")
    response = {
        "urs" : urs_report,
        "frs" : frs_report
    }
    return response

@app.get("/frs_report")
async def frs_reporter():
    frs_path = "gxpgenie"
    frs_vectorstore = await create_rag_model(frs_path,"reports/Sample_URS.pdf")
    frs_report = await model_call(frs_vectorstore, FRS_prompt(), "Generate Detailed Report Analysis")
    response = {
        "frs" : frs_report
    }
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
