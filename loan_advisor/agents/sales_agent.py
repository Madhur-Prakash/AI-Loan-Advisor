from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class SalesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Sales Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        context = self.get_context(application)
        
        if not application.loan_amount:
            llm_response = await self.llm.generate_response(self.name, context, "Ask for loan amount")
            return AgentResponse(
                agent_name=self.name,
                message=llm_response,
                action_required="collect_loan_amount"
            )
        
        if not application.tenure_months:
            context["loan_amount"] = application.loan_amount
            llm_response = await self.llm.generate_response(self.name, context, "Ask for tenure preference")
            return AgentResponse(
                agent_name=self.name,
                message=llm_response,
                action_required="collect_tenure"
            )
        
        # Set interest rate based on loan amount
        if application.loan_amount <= 500000:
            interest_rate = 10.5
        elif application.loan_amount <= 1000000:
            interest_rate = 11.5
        else:
            interest_rate = 12.5
        
        emi = self.calculate_emi(application.loan_amount, interest_rate, application.tenure_months)
        
        context.update({
            "loan_amount": application.loan_amount,
            "tenure_months": application.tenure_months,
            "interest_rate": interest_rate,
            "emi": emi
        })
        
        llm_response = await self.llm.generate_response(self.name, context, "Present loan summary and move to verification")
        
        return AgentResponse(
            agent_name=self.name,
            message=llm_response,
            next_agent="verification_agent",
            data_updates={
                "interest_rate": interest_rate,
                "emi": emi,
                "status": LoanStatus.KYC_VERIFICATION.value
            }
        )