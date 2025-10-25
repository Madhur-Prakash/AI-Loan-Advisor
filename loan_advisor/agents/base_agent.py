from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.loan_models import LoanApplication, AgentResponse
from services.llm_service import LLMService

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.llm = LLMService()
    
    @abstractmethod
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        pass
    
    def calculate_emi(self, principal: float, rate: float, tenure_months: int) -> float:
        monthly_rate = rate / (12 * 100)
        emi = principal * monthly_rate * (1 + monthly_rate)**tenure_months / ((1 + monthly_rate)**tenure_months - 1)
        return round(emi, 2)
    
    def get_context(self, application: LoanApplication) -> Dict[str, Any]:
        return {
            "customer_name": application.customer.name,
            "status": application.status.value,
            "loan_amount": application.loan_amount,
            "credit_score": application.customer.credit_score,
            "emi": application.emi,
            "tenure_months": application.tenure_months
        }