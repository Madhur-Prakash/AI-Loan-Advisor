import random
import re
from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class VerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Verification Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        # Ensure name is captured before KYC
        if not application.customer.name:
            return AgentResponse(
                agent_name=self.name,
                message=(
                    "Before we begin KYC, please share your full name. "
                    "You can say: 'My name is <Your Name>'"
                ),
                action_required="collect_name"
            )

        # Validate any provided/attempted PAN/Aadhar formats and aggregate errors
        errors: list[str] = []
        pan_to_check = application.customer.pan or self._find_pan_attempt(message)
        if pan_to_check and not self._is_valid_pan(pan_to_check):
            errors.append("Invalid PAN format")
        aadhar_to_check = application.customer.aadhar or self._find_aadhar_attempt(message)
        if aadhar_to_check and not self._is_valid_aadhar(aadhar_to_check):
            errors.append("Invalid Aadhar format")

        if errors:
            err_msg = ""
            if "Invalid PAN format" in errors:
                err_msg += (
                    f"❌ **Invalid PAN Format Detected:** '{pan_to_check}'\n\n"
                    "📋 **Correct PAN Format:** ABCDE1234F\n"
                    "   • First 5 characters: Uppercase letters (A-Z)\n"
                    "   • Next 4 characters: Digits (0-9)\n"
                    "   • Last character: Uppercase letter (A-Z)\n"
                    "   • Example: ABCDE1234F\n\n"
                )
            if "Invalid Aadhar format" in errors:
                err_msg += (
                    f"❌ **Invalid Aadhar Format Detected:** '{aadhar_to_check}'\n\n"
                    "📋 **Correct Aadhar Format:** 12 digits only\n"
                    "   • Must be exactly 12 digits\n"
                    "   • No spaces or special characters\n"
                    "   • Example: 123456789012\n\n"
                )
            err_msg += "Please re-enter the correct details in the required format."
            
            return AgentResponse(
                agent_name=self.name,
                message=err_msg,
                action_required=(
                    "collect_pan_aadhar" if len(errors) == 2
                    else ("collect_pan" if "Invalid PAN format" in errors else "collect_aadhar")
                )
            )
        
        # If PAN not captured yet, request it
        if not application.customer.pan:
            return AgentResponse(
                agent_name=self.name,
                message="For KYC verification, please provide your PAN number:",
                action_required="collect_pan"
            )

        # If Aadhar not captured yet, request it
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
                message="✅ KYC verification successful! Your identity has been verified. "
                       "Now let's check your credit profile.",
                next_agent="underwriting_agent",
                data_updates={"status": LoanStatus.UNDERWRITING.value}
            )
        else:
            return AgentResponse(
                agent_name=self.name,
                message=(
                    "❌ **KYC Verification Failed**\n\n"
                    "**Reason:** Unable to verify your identity with the provided documents.\n\n"
                    "**Possible Issues:**\n"
                    "• PAN or Aadhar details don't match government records\n"
                    "• Documents may be inactive or blacklisted\n"
                    "• Name mismatch between PAN and Aadhar\n\n"
                    "**What you can do:**\n"
                    "• Double-check your PAN and Aadhar numbers\n"
                    "• Ensure your documents are active and updated\n"
                    "• Contact SYNFIN support for manual verification\n"
                    "• Try again with correct details\n\n"
                    f"A detailed email has been sent to {application.customer.email or 'your registered email'}."
                ),
                data_updates={
                    "status": LoanStatus.REJECTED.value,
                    "rejection_reason": "KYC verification failed - Unable to verify identity with provided documents"
                }
            )
    
    def _mock_kyc_verification(self, pan: str, aadhar: str) -> bool:
        # Mock API call - 95% success rate
        return random.random() > 0.05

    # === Helpers ===
    def _is_valid_pan(self, pan: str) -> bool:
        """Valid PAN: 5 uppercase letters, 4 digits, 1 uppercase letter."""
        return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", (pan or "").upper()))

    def _is_valid_aadhar(self, aadhar: str) -> bool:
        """Valid Aadhar: exactly 12 digits."""
        return bool(re.fullmatch(r"\d{12}", aadhar or ""))

    def _find_pan_attempt(self, message: str) -> str | None:
        """Try to find a PAN-like token in the message when user mentions PAN."""
        msg = message or ""
        if re.search(r"\bpan\b", msg.lower()):
            m = re.search(r"\b([A-Z0-9]{10})\b", msg.upper())
            if m:
                return m.group(1)
        return None

    def _find_aadhar_attempt(self, message: str) -> str | None:
        """Find a sequence of 10–14 digits when user mentions Aadhar or provides digits."""
        msg = message or ""
        if re.search(r"\baadhar|aadhaar\b", msg.lower()) or re.search(r"\b\d{10,14}\b", msg):
            m = re.search(r"\b(\d{10,14})\b", msg)
            if m:
                return m.group(1)
        return None