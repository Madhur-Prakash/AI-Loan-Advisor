from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class LoanStatus(str, Enum):
    INITIATED = "initiated"
    SALES_DISCUSSION = "sales_discussion"
    KYC_VERIFICATION = "kyc_verification"
    UNDERWRITING = "underwriting"
    ELIGIBILITY_CHECK = "eligibility_check"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class Customer(BaseModel):
    customer_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    pan: Optional[str] = None
    aadhar: Optional[str] = None
    salary: Optional[float] = None
    credit_score: Optional[int] = None

class LoanApplication(BaseModel):
    application_id: str
    customer: Customer
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    status: LoanStatus = LoanStatus.INITIATED
    pre_approved_limit: Optional[float] = None
    emi: Optional[float] = None
    rejection_reason: Optional[str] = None
    sanction_letter_path: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    sender: str
    timestamp: str

class AgentResponse(BaseModel):
    agent_name: str
    message: str
    next_agent: Optional[str] = None
    action_required: Optional[str] = None
    data_updates: Optional[Dict[str, Any]] = None