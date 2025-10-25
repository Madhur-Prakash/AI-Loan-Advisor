import random
from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class VerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Verification Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        if not application.customer.pan:
            return AgentResponse(
                agent_name=self.name,
                message="For KYC verification, please provide your PAN number:",
                action_required="collect_pan"
            )
        
        if not application.customer.aadhar:
            return AgentResponse(
                agent_name=self.name,
                message="Thank you! Now please provide your Aadhar number:",
                action_required="collect_aadhar"
            )
        
        # Mock KYC verification
        kyc_success = self._mock_kyc_verification(application.customer.pan, application.customer.aadhar)
        
        if kyc_success:
            return AgentResponse(
                agent_name=self.name,
                message="KYC verification successful! Your identity has been verified. "
                       "Now let's check your credit profile.",
                next_agent="underwriting_agent",
                data_updates={"status": LoanStatus.UNDERWRITING.value}
            )
        else:
            return AgentResponse(
                agent_name=self.name,
                message="KYC verification failed. Please check your details and try again.",
                data_updates={
                    "status": LoanStatus.REJECTED.value,
                    "rejection_reason": "KYC verification failed"
                }
            )
    
    def _mock_kyc_verification(self, pan: str, aadhar: str) -> bool:
        # Mock API call - 95% success rate
        return random.random() > 0.05