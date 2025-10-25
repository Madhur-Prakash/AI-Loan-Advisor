from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.services.loan_orchestrator import LoanOrchestrator

app = FastAPI(title="AI Loan Processing API", version="1.0.0")
orchestrator = LoanOrchestrator()

class ChatRequest(BaseModel):
    customer_id: str
    message: str
    application_id: Optional[str] = None
    data_update: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    application_id: str
    agent_name: str
    message: str
    status: str
    action_required: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if request.application_id:
            # Continue existing conversation
            result = await orchestrator.process_message(
                request.application_id, 
                request.message, 
                request.data_update
            )
            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])
            
            return ChatResponse(
                application_id=request.application_id,
                agent_name=result["agent_name"],
                message=result["message"],
                status=result["status"],
                action_required=result.get("action_required")
            )
        else:
            # Start new conversation
            result = await orchestrator.start_application(request.customer_id, request.message)
            response_data = result["response"]
            
            return ChatResponse(
                application_id=result["application_id"],
                agent_name=response_data["agent_name"],
                message=response_data["message"],
                status=response_data["status"],
                action_required=response_data.get("action_required")
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/application/{app_id}")
async def get_application(app_id: str):
    application = orchestrator.get_application(app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application.dict()

@app.get("/sanction-letter/{app_id}")
async def download_sanction_letter(app_id: str):
    application = orchestrator.get_application(app_id)
    if not application or not application.sanction_letter_path:
        raise HTTPException(status_code=404, detail="Sanction letter not found")
    
    if not os.path.exists(application.sanction_letter_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=application.sanction_letter_path,
        filename=f"sanction_letter_{app_id}.pdf",
        media_type="application/pdf"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Loan Processing API"}

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Loan Processing API"}