from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class MasterAgent(BaseAgent):
    def __init__(self):
        super().__init__("Master Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        context = self.get_context(application)
        
        if application.status == LoanStatus.INITIATED:
            if not application.customer.name:
                llm_response = await self.llm.generate_response(self.name, context, message)
                return AgentResponse(
                    agent_name=self.name,
                    message=llm_response,
                    action_required="collect_name"
                )
            
            llm_response = await self.llm.generate_response(self.name, context, "Customer wants to explore loan options")
            return AgentResponse(
                agent_name=self.name,
                message=llm_response,
                next_agent="sales_agent",
                data_updates={"status": LoanStatus.SALES_DISCUSSION.value}
            )
        
        llm_response = await self.llm.generate_response(self.name, context, "Connect to sales agent")
        return AgentResponse(
            agent_name=self.name,
            message=llm_response,
            next_agent="sales_agent"
        )