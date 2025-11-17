import uuid
from typing import Dict, Any, Optional
import re
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.master_agent import MasterAgent
from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.eligibility_agent import EligibilityAgent
from agents.pdf_agent import PDFAgent
from models.loan_models import LoanApplication, Customer, LoanStatus, AgentResponse

class LoanOrchestrator:
    def __init__(self):
        self.agents = {
            "master_agent": MasterAgent(),
            "sales_agent": SalesAgent(),
            "verification_agent": VerificationAgent(),
            "underwriting_agent": UnderwritingAgent(),
            "eligibility_agent": EligibilityAgent(),
            "pdf_agent": PDFAgent()
        }
        self.applications: Dict[str, LoanApplication] = {}
    
    async def start_application(self, customer_id: str, initial_message: str = "") -> Dict[str, Any]:
        app_id = str(uuid.uuid4())
        application = LoanApplication(
            application_id=app_id,
            customer=Customer(customer_id=customer_id)
        )
        
        self.applications[app_id] = application
        
        response = await self.process_message(app_id, initial_message or "Hello")
        return {
            "application_id": app_id,
            "response": response
        }
    
    async def process_message(self, app_id: str, message: str, data_update: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if app_id not in self.applications:
            return {"error": "Application not found"}
        
        application = self.applications[app_id]
        
        # Update application data if provided
        if data_update:
            self._update_application_data(application, data_update)
        
        # Parse message for data extraction
        self._extract_data_from_message(application, message)

        # Route to appropriate agent based on user intent keywords
        self._route_by_intent(application, message)
        
        # Get current agent based on status
        current_agent = self._get_current_agent(application)
        
        # Process with agent
        response = await current_agent.process(application, message)
        
        # Update application with response data
        if response.data_updates:
            self._update_application_data(application, response.data_updates)
        
        # Check if we need to move to next agent
        if response.next_agent and response.next_agent in self.agents:
            next_agent = self.agents[response.next_agent]
            next_response = await next_agent.process(application, "")
            if next_response.message:
                # Avoid duplicating salutations when chaining agents (e.g., Master → Sales)
                deduped = self._dedupe_greeting(response.message or "", next_response.message or "")
                if deduped:
                    response.message += "\n\n" + deduped
            if next_response.data_updates:
                self._update_application_data(application, next_response.data_updates)
        
        return {
            "agent_name": response.agent_name,
            "message": response.message,
            "status": application.status.value,
            "action_required": response.action_required,
            "application_data": application.dict()
        }

    def _dedupe_greeting(self, first_msg: str, second_msg: str) -> str:
        """If both messages begin with a greeting, strip the salutation from the second.
        Keeps the content while removing repeated "Hello/Hi/Welcome" style openers.
        """

        def has_greeting(text: str) -> bool:
            return bool(re.match(r"^\s*(hello|hi|hey|welcome)\b", text.strip(), re.IGNORECASE))

        def strip_leading_greeting(text: str) -> str:
            # Remove leading greeting sentence like: "Hello Ansh, ..." up to the first sentence end.
            cleaned = re.sub(r"^\s*(hello|hi|hey|welcome)[^.!?]*[.!?]\s*", "", text.strip(), flags=re.IGNORECASE)
            # Also trim common courtesy openers
            cleaned = re.sub(r"^(thank you for (considering|choosing)\s+synfin[^.!?]*[.!?]\s*)", "", cleaned, flags=re.IGNORECASE)
            return cleaned or text.strip()

        if has_greeting(first_msg) and has_greeting(second_msg):
            return strip_leading_greeting(second_msg)
        return second_msg
    
    def _get_current_agent(self, application: LoanApplication):
        status_agent_map = {
            LoanStatus.INITIATED: "master_agent",
            LoanStatus.SALES_DISCUSSION: "sales_agent",
            LoanStatus.KYC_VERIFICATION: "verification_agent",
            LoanStatus.UNDERWRITING: "underwriting_agent",
            LoanStatus.ELIGIBILITY_CHECK: "eligibility_agent",
            LoanStatus.APPROVED: "pdf_agent"
        }
        
        agent_name = status_agent_map.get(application.status, "master_agent")
        return self.agents[agent_name]
    
    def _update_application_data(self, application: LoanApplication, updates: Dict[str, Any]):
        for key, value in updates.items():
            if key == "status":
                application.status = LoanStatus(value)
            elif hasattr(application, key):
                setattr(application, key, value)
            elif hasattr(application.customer, key):
                setattr(application.customer, key, value)
    
    def _extract_data_from_message(self, application: LoanApplication, message: str):
        message_lower = message.lower()
        
        # Extract name
        if not application.customer.name and any(word in message_lower for word in ["my name is", "i am", "i'm"]):
            parts = message.split()
            for i, part in enumerate(parts):
                if part.lower() in ["is", "am"] and i + 1 < len(parts):
                    application.customer.name = parts[i + 1].strip(".,!?")
                    break
        
        # Extract loan amount
        if not application.loan_amount:
            import re
            amount_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lakhs|crore|crores)?', message)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                amount = float(amount_str)
                if 'lakh' in message_lower:
                    amount *= 100000
                elif 'crore' in message_lower:
                    amount *= 10000000
                application.loan_amount = amount
        
        
        # Case A: explicit unit provided (always allow update if present in message)
        tenure_match = re.search(r'(\d+)\s*(months?|month|years?|yrs?|y)\b', message_lower)
        if tenure_match:
            tenure = int(tenure_match.group(1))
            unit = tenure_match.group(2)
            if unit.startswith('y') or unit.startswith('yr') or unit.startswith('year'):
                tenure *= 12
            application.tenure_months = tenure
        else:
            # Case B: directive patterns like "tenure to <n> months"
            dir_match = re.search(r'(?:tenure\s*(?:to|is|=)\s*)(\d{1,3})\s*(months?|month|years?|yrs?|y)\b', message_lower)
            if dir_match:
                n = int(dir_match.group(1))
                unit = dir_match.group(2)
                if unit.startswith('y') or unit.startswith('yr') or unit.startswith('year'):
                    n *= 12
                application.tenure_months = n
            else:
                # Case C: fallback bare number interpreted as months when tenure not yet set
                if not application.tenure_months:
                    bare_match = re.search(r'\b(\d{1,3})\b', message_lower)
                    if bare_match:
                        n = int(bare_match.group(1))
                        if 6 <= n <= 120:
                            application.tenure_months = n
        
        # Extract PAN
        if not application.customer.pan:
            import re
            pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', message.upper())
            if pan_match:
                application.customer.pan = pan_match.group()
        
        # Extract Aadhar
        if not application.customer.aadhar:
            import re
            aadhar_match = re.search(r'\b\d{12}\b', message)
            if aadhar_match:
                application.customer.aadhar = aadhar_match.group()
        
        # Extract salary
        if not application.customer.salary:
            import re
            # Support lakh/crore units and month/year qualifiers
            def to_rupees(num_str: str, unit: Optional[str]) -> float:
                try:
                    base = float(num_str.replace(',', ''))
                except Exception:
                    return float('nan')
                if not unit:
                    return base
                u = unit.lower()
                if re.search(r'crore|crores', u):
                    return base * 10000000
                if re.search(r'lakh|lakhs|lac|lacs|lkhs|lkh', u):
                    return base * 100000
                return base

            is_monthly = bool(re.search(r'\b(month|monthly|per\s*month|a\s*month)\b', message_lower))
            is_yearly = bool(re.search(r'\b(year|yearly|per\s*year|annum|annual|p\.?a\.?)\b', message_lower))

            # Case 1: explicit salary mention
            salary_match = re.search(r'salary[^\d]*(\d[\d,]*)(?:\s*)(lakh|lakhs|lac|lacs|lkhs|lkh|crore|crores)?', message, re.IGNORECASE)
            if salary_match:
                value = to_rupees(salary_match.group(1), salary_match.group(2))
                if value == value:  # not NaN
                    application.customer.salary = value if is_monthly or not is_yearly else round(value / 12)
                    return

            # Case 2: generic amount near monthly/yearly context
            generic_match = re.search(r'(\d[\d,]*)(?:\s*)(lakh|lakhs|lac|lacs|lkhs|lkh|crore|crores)?', message, re.IGNORECASE)
            if generic_match and ('salary' in message_lower or is_monthly or is_yearly):
                value = to_rupees(generic_match.group(1), generic_match.group(2))
                if value == value:
                    application.customer.salary = value if is_monthly or not is_yearly else round(value / 12)

    def _route_by_intent(self, application: LoanApplication, message: str):
        """Adjust application status based on message intent to switch agents appropriately.
        Minimal, keyword-based routing to improve user experience.
        """
        ml = message.lower()

        # Gate: Always collect customer name before progressing to sales/KYC/underwriting/eligibility/pdf
        # If name is missing, keep the flow with the Master Agent to collect it.
        if not application.customer.name:
            application.status = LoanStatus.INITIATED
            return
        # Sales-related intents: EMI, interest, tenure, loan amount
        sales_intent = any(k in ml for k in [
            'emi', 'interest', 'rate', 'tenure', 'months', 'years', 'loan', 'amount', 'rupees', '₹', 'lakh', 'crore',
            'repayment', 'repay', 'installment', 'schedule', 'plan', 'plans', 'options'
        ])
        # Verification-related intents: PAN/Aadhar/KYC
        import re
        pan_intent = ('pan' in ml) or bool(re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', message.upper()))
        aadhar_intent = ('aadhar' in ml) or bool(re.search(r'\b\d{12}\b', message))
        # Only treat generic 'kyc' as verification intent once core sales details are complete
        verification_intent = pan_intent or aadhar_intent or (
            ('kyc' in ml) and bool(application.loan_amount) and bool(application.tenure_months)
        )
        # Underwriting intent
        underwriting_intent = ('credit score' in ml) or ('underwriting' in ml)
        # Eligibility intent
        eligibility_intent = ('eligibility' in ml) or ('approve' in ml) or ('approval' in ml) or ('salary' in ml)
        # PDF intent
        pdf_intent = ('sanction letter' in ml) or ('pdf' in ml)

        # Prefer verification when PAN/Aadhar provided or explicit KYC requested after sales details
        if verification_intent:
            application.status = LoanStatus.KYC_VERIFICATION
            return

        # Route to sales if discussing EMI/tenure/amount and still in early stages
        if sales_intent and application.status in {LoanStatus.INITIATED, LoanStatus.SALES_DISCUSSION, LoanStatus.KYC_VERIFICATION}:
            application.status = LoanStatus.SALES_DISCUSSION
            return

        # Route to underwriting if explicitly requested and KYC done
        if underwriting_intent and application.status in {LoanStatus.KYC_VERIFICATION, LoanStatus.UNDERWRITING, LoanStatus.ELIGIBILITY_CHECK}:
            application.status = LoanStatus.UNDERWRITING
            return

        # Route to eligibility if discussing approval/salary and underwriting complete
        if eligibility_intent and application.status in {LoanStatus.UNDERWRITING, LoanStatus.ELIGIBILITY_CHECK, LoanStatus.APPROVED}:
            application.status = LoanStatus.ELIGIBILITY_CHECK
            return

        # Route to PDF agent if asking for sanction letter and already approved
        if pdf_intent and application.status in {LoanStatus.APPROVED, LoanStatus.COMPLETED}:
            application.status = LoanStatus.APPROVED
    
    def get_application(self, app_id: str) -> Optional[LoanApplication]:
        return self.applications.get(app_id)