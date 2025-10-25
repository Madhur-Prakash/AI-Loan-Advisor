import random
from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class UnderwritingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Underwriting Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        # Fetch credit score (mock)
        credit_score = self._fetch_credit_score(application.customer.pan)
        
        # Set pre-approved limit based on credit score
        if credit_score >= 750:
            pre_approved_limit = 1000000
        elif credit_score >= 700:
            pre_approved_limit = 500000
        elif credit_score >= 650:
            pre_approved_limit = 300000
        else:
            pre_approved_limit = 100000
        
        return AgentResponse(
            agent_name=self.name,
            message=f"Credit assessment completed!\n"
                   f"Credit Score: {credit_score}\n"
                   f"Pre-approved Limit: ₹{pre_approved_limit:,.0f}\n\n"
                   f"Proceeding to eligibility check...",
            next_agent="eligibility_agent",
            data_updates={
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit,
                "status": LoanStatus.ELIGIBILITY_CHECK.value
            }
        )
    
    def _fetch_credit_score(self, pan: str) -> int:
        # Mock credit score generation (600-800 range)
        return random.randint(600, 800)