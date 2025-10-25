from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class EligibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("Eligibility Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        # Check if loan amount is within pre-approved limit and credit score >= 700
        if (application.loan_amount <= application.pre_approved_limit and 
            application.customer.credit_score >= 700):
            
            return AgentResponse(
                agent_name=self.name,
                message=f"🎉 Congratulations! Your loan of ₹{application.loan_amount:,.0f} is INSTANTLY APPROVED!\n"
                       f"Processing your sanction letter...",
                next_agent="pdf_agent",
                data_updates={"status": LoanStatus.APPROVED.value}
            )
        
        # If loan exceeds limit or credit score is lower, request salary slip
        if not application.customer.salary:
            return AgentResponse(
                agent_name=self.name,
                message="To proceed with your application, please provide your monthly salary:",
                action_required="collect_salary"
            )
        
        # Check EMI to salary ratio (should be <= 50%)
        emi_ratio = (application.emi / application.customer.salary) * 100
        
        if emi_ratio <= 50:
            return AgentResponse(
                agent_name=self.name,
                message=f"Great! Your EMI-to-salary ratio is {emi_ratio:.1f}% (within acceptable limits).\n"
                       f"Your loan of ₹{application.loan_amount:,.0f} is APPROVED!\n"
                       f"Generating your sanction letter...",
                next_agent="pdf_agent",
                data_updates={"status": LoanStatus.APPROVED.value}
            )
        else:
            return AgentResponse(
                agent_name=self.name,
                message=f"Unfortunately, your EMI-to-salary ratio is {emi_ratio:.1f}% which exceeds our "
                       f"maximum limit of 50%. Your loan application has been rejected.",
                data_updates={
                    "status": LoanStatus.REJECTED.value,
                    "rejection_reason": f"EMI-to-salary ratio too high: {emi_ratio:.1f}%"
                }
            )