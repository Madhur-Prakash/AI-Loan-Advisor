from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse 
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.services.send_email import send_email_with_url_attachment, send_email_with_aiosmtplib
from loan_advisor.services.loan_orchestrator import LoanOrchestrator
from tests.generate_sample_pdf import generate_sample

app = FastAPI(title="AI Loan Processing API", version="1.0.0")

#  middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8082",
        "http://127.0.0.1:8082",
        "https://synfin.vercel.app",
        os.getenv("AWS_EC2_URL", "http://localhost:8000"),
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    if application.sanction_letter_path.startswith("http://") or application.sanction_letter_path.startswith("https://"): 
        return RedirectResponse(url=application.sanction_letter_path, status_code=307)

    
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

@app.post("/test-pdf-on-server")
async def test_pdf_on_server():
    try:
        res = await generate_sample()
        return {"message": "Sample sanction letter generated successfully on server.", "Document": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-email")
async def test_email():
    try:
        to_email = os.getenv("TEST_EMAIL_RECIPIENT")
        subject = "Test Email"
        body = "<h1>This is a test email</h1><p>Sent using Gmail API</p>"
        await send_email_with_url_attachment(to_email, subject, body, file_path="https://fra.cloud.appwrite.io/v1/storage/buckets/6856b5e8002828b1fe22/files/06c47a6c-a408-4e34-bb66-e05fe7b14be1/view?project=6856b323003243cb7206&mode=admin")
        return {"message": "Test email sent successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))