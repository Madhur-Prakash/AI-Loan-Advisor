from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus
import os
from dotenv import load_dotenv
import re

load_dotenv()
API_ENDPOINT = os.getenv("API_ENDPOINT")
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_ID = os.getenv("BUCKET_ID")

class EligibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("Eligibility Agent")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        ml = (message or "").lower()

        # Accept user adjustments to tenure or amount and recompute EMI before eligibility decision
        updated_fields = {}

        # Tenure updates like: "increase tenure to 69 months", "tenure to 48", "for 60 months"
        tmatch = re.search(r'(\d+)\s*(months?|month|years?|yrs?|y)\b', ml)
        if tmatch:
            tval = int(tmatch.group(1))
            unit = tmatch.group(2)
            if unit.startswith('y') or unit.startswith('yr') or unit.startswith('year'):
                tval *= 12
            application.tenure_months = tval
            updated_fields["tenure_months"] = tval
        else:
            dirmatch = re.search(r'(?:tenure\s*(?:to|is|=)\s*)(\d{1,3})\s*(months?|month|years?|yrs?|y)\b', ml)
            if dirmatch:
                n = int(dirmatch.group(1))
                unit = dirmatch.group(2)
                if unit.startswith('y') or unit.startswith('yr') or unit.startswith('year'):
                    n *= 12
                application.tenure_months = n
                updated_fields["tenure_months"] = n

        # Amount updates like: "reduce amount to 300000", "loan amount 3 lakhs"
        amatch = re.search(r'(?:amount|loan\s*amount)[^\d]*(\d[\d,]*)(?:\s*)(lakh|lakhs|lac|lacs|lkhs|lkh|crore|crores)?', message, re.IGNORECASE)
        if amatch:
            raw = amatch.group(1).replace(',', '')
            try:
                base = float(raw)
            except Exception:
                base = None
            unit = amatch.group(2).lower() if amatch.group(2) else None
            if base is not None:
                if unit:
                    if re.search(r'crore|crores', unit):
                        base *= 10000000
                    elif re.search(r'lakh|lakhs|lac|lacs|lkhs|lkh', unit):
                        base *= 100000
                application.loan_amount = base
                updated_fields["loan_amount"] = base

        # If terms changed, recompute rate slab and EMI deterministically
        def calc_emi(p: float, annual_rate: float, n: int) -> float:
            r = (annual_rate or 0) / 12 / 100
            if r <= 0 or n <= 0:
                return p / max(n, 1)
            pow_val = (1 + r) ** n
            return p * r * pow_val / (pow_val - 1)

        if updated_fields:
            # Determine interest rate slab from amount
            if application.loan_amount is not None:
                if application.loan_amount <= 500000:
                    interest_rate = 10.5
                elif application.loan_amount <= 1000000:
                    interest_rate = 11.5
                else:
                    interest_rate = 12.5
            else:
                interest_rate = application.interest_rate or 11.5

            if application.loan_amount and application.tenure_months:
                emi = calc_emi(application.loan_amount, interest_rate, int(application.tenure_months))
                application.interest_rate = interest_rate
                application.emi = emi
                updated_fields["interest_rate"] = interest_rate
                updated_fields["emi"] = emi

        # If user gave an affirmative reply without explicit numbers, auto-apply best suggestion
        if not updated_fields:
            affirmative = any(
                phrase in ml for phrase in [
                    "yes", "ok", "okay", "sure", "do that", "do it", "proceed", "go ahead", "please do"
                ]
            )
            if affirmative:
                # Recompute suggestions based on current state
                salary = application.customer.salary or 0
                loan_amount = application.loan_amount or 0
                annual_rate = application.interest_rate
                # If interest_rate not set yet, infer slab from amount
                if annual_rate is None:
                    if loan_amount <= 500000:
                        annual_rate = 10.5
                    elif loan_amount <= 1000000:
                        annual_rate = 11.5
                    else:
                        annual_rate = 12.5
                rate = (annual_rate or 0) / 12 / 100
                tenure = int(application.tenure_months or 0)

                def emi_for(p: float, r: float, n: int) -> float:
                    if r <= 0 or n <= 0:
                        return p / max(n, 1)
                    pow_val = (1 + r) ** n
                    return p * r * pow_val / (pow_val - 1)

                target_emi = salary * 0.5
                suggested_tenure = None
                suggested_emi = None
                if rate > 0 and loan_amount > 0:
                    for n in range(max(tenure, 12), 121):
                        e = emi_for(loan_amount, rate, n)
                        if e <= target_emi:
                            suggested_tenure = n
                            suggested_emi = e
                            break

                suggested_amount = None
                if rate > 0 and tenure > 0:
                    pow_val = (1 + rate) ** tenure
                    k = rate * pow_val / (pow_val - 1) if pow_val > 1 else (rate or 1)
                    if k > 0:
                        suggested_amount = target_emi / k
                        if suggested_amount < 50000:
                            suggested_amount = None

                # Prefer tenure increase if available; else reduce amount within pre-approved cap
                if suggested_tenure:
                    application.tenure_months = suggested_tenure
                    application.interest_rate = annual_rate
                    application.emi = calc_emi(loan_amount, annual_rate, suggested_tenure)
                    updated_fields["tenure_months"] = suggested_tenure
                    updated_fields["interest_rate"] = annual_rate
                    updated_fields["emi"] = application.emi
                elif suggested_amount:
                    cap = application.pre_approved_limit or suggested_amount
                    amt = min(suggested_amount, cap)
                    application.loan_amount = amt
                    # Recompute slab after amount change
                    if application.loan_amount <= 500000:
                        annual_rate = 10.5
                    elif application.loan_amount <= 1000000:
                        annual_rate = 11.5
                    else:
                        annual_rate = 12.5
                    application.interest_rate = annual_rate
                    if application.tenure_months:
                        application.emi = calc_emi(application.loan_amount, annual_rate, int(application.tenure_months))
                        updated_fields["emi"] = application.emi
                    updated_fields["loan_amount"] = application.loan_amount
                    updated_fields["interest_rate"] = annual_rate
        # Check if loan amount is within pre-approved limit and credit score >= 700
        if (application.loan_amount <= application.pre_approved_limit and 
            application.customer.credit_score >= 700):
            
            return AgentResponse(
                agent_name=self.name,
                message=f"🎉 Congratulations! Your loan of ₹{application.loan_amount:,.0f} is INSTANTLY APPROVED by SYNFIN!\n"
                       f"Processing your SYNFIN sanction letter...",
                next_agent="pdf_agent",
                data_updates={"status": LoanStatus.APPROVED.value}
            )
        
        # If loan exceeds limit or credit score is lower, request salary slip
        if not application.customer.salary or application.customer.salary <= 0:
            return AgentResponse(
                agent_name=self.name,
                message="To proceed with your application at SYNFIN, please provide your monthly salary:",
                action_required="collect_salary"
            )
        
        # Check EMI to salary ratio (should be <= 50%)
        emi_ratio = (application.emi / application.customer.salary) * 100 if application.customer.salary else float('inf')
        # Detect anomalies: extremely high ratios or implausibly low salary indicate parsing issues
        if application.customer.salary and (application.customer.salary < 5000 or emi_ratio > 1000):
            return AgentResponse(
                agent_name=self.name,
                message=(
                    "I might have misread your salary, which is causing an unrealistic EMI-to-salary ratio.\n"
                    "Please reconfirm your monthly salary in rupees, e.g.:\n"
                    "• My monthly salary is 60,000\n"
                    "• Salary 12 lakhs per annum (we’ll convert to monthly)"
                ),
                action_required="collect_salary"
            )
        
        if emi_ratio <= 50:
            return AgentResponse(
                agent_name=self.name,
                message=(
                    (
                        f"Updated terms accepted. Tenure: {application.tenure_months} months. "
                        f"EMI: ₹{application.emi:,.0f}.\n"
                    ) if updated_fields else ""
                ) +
                       f"Great! Your EMI-to-salary ratio is {emi_ratio:.1f}% (within acceptable limits).\n"
                       f"Your loan of ₹{application.loan_amount:,.0f} is APPROVED by SYNFIN!\n"
                       f"Generating your SYNFIN sanction letter...",
                next_agent="pdf_agent",
                data_updates={"status": LoanStatus.APPROVED.value, **updated_fields}
            )
        else:
            # Compute actionable suggestions
            salary = application.customer.salary or 0
            loan_amount = application.loan_amount or 0
            rate = (application.interest_rate or 0) / 12 / 100  # monthly rate
            tenure = int(application.tenure_months or 0)

            def emi_for(p: float, r: float, n: int) -> float:
                if r <= 0 or n <= 0:
                    return p / max(n, 1)
                pow_val = (1 + r) ** n
                return p * r * pow_val / (pow_val - 1)

            target_emi = salary * 0.5
            suggested_tenure = None
            suggested_emi = None
            if rate > 0 and loan_amount > 0:
                # Try increasing tenure up to 120 months to meet target EMI
                for n in range(max(tenure, 12), 121):
                    e = emi_for(loan_amount, rate, n)
                    if e <= target_emi:
                        suggested_tenure = n
                        suggested_emi = e
                        break

            suggested_amount = None
            if rate > 0 and tenure > 0:
                # Compute max principal for current tenure such that EMI <= target
                pow_val = (1 + rate) ** tenure
                k = rate * pow_val / (pow_val - 1) if pow_val > 1 else (rate or 1)
                if k > 0:
                    suggested_amount = target_emi / k
                    # Omit unrealistic tiny amounts which likely stem from misparsed salary
                    if suggested_amount < 50000:
                        suggested_amount = None

            # Build detailed rejection message
            rejection_msg = (
                f"❌ **Loan Application Rejected**\n\n"
                f"📊 **Rejection Reason:**\n"
                f"Your EMI-to-salary ratio is {emi_ratio:.1f}%, which exceeds SYNFIN's maximum limit of 50%.\n\n"
                f"💰 **Current Details:**\n"
                f"• Loan Amount: ₹{loan_amount:,.0f}\n"
                f"• Monthly EMI: ₹{application.emi:,.0f}\n"
                f"• Monthly Salary: ₹{salary:,.0f}\n"
                f"• Tenure: {tenure} months\n"
                f"• Interest Rate: {application.interest_rate}% p.a.\n\n"
                f"🔄 **Negotiation Options to Get Approved:**\n\n"
            )

            # Add specific actionable suggestions
            if suggested_tenure and suggested_emi is not None:
                rejection_msg += (
                    f"✅ **Option 1: Increase Tenure**\n"
                    f"   Extend to {suggested_tenure} months\n"
                    f"   New EMI: ₹{suggested_emi:,.0f} (within 50% limit)\n"
                    f"   Say: 'Increase tenure to {suggested_tenure} months'\n\n"
                )
            
            if suggested_amount:
                cap = application.pre_approved_limit or suggested_amount
                amt = min(suggested_amount, cap)
                rejection_msg += (
                    f"✅ **Option 2: Reduce Loan Amount**\n"
                    f"   Lower to ₹{amt:,.0f}\n"
                    f"   Keep current {tenure}-month tenure\n"
                    f"   Say: 'Reduce amount to {int(amt)}'\n\n"
                )
            
            # Add negotiation with sales agent option
            rejection_msg += (
                f"✅ **Option 3: Negotiate Better Rate**\n"
                f"   Request lower interest rate to reduce EMI\n"
                f"   Say: 'Can I get a better interest rate?'\n\n"
                f"✅ **Option 4: Increase Income Proof**\n"
                f"   Add co-applicant income\n"
                f"   Include additional income sources\n"
                f"   Provide updated salary details\n\n"
            )

            if application.pre_approved_limit and loan_amount > application.pre_approved_limit:
                rejection_msg += (
                    f"⚠️ **Note:** Your pre-approved limit is ₹{application.pre_approved_limit:,.0f}. "
                    f"Consider staying within this limit for faster approval.\n\n"
                )

            rejection_msg += (
                f"💬 **Ready to try again?** Share your preferred option or ask me to recalculate!"
            )

            return AgentResponse(
                agent_name=self.name,
                message=rejection_msg,
                data_updates={
                    "status": LoanStatus.REJECTED.value,
                    "rejection_reason": f"EMI-to-salary ratio {emi_ratio:.1f}% exceeds 50% limit. Suggested: Increase tenure to {suggested_tenure} months or reduce amount to ₹{suggested_amount:,.0f}" if suggested_amount else f"EMI-to-salary ratio {emi_ratio:.1f}% exceeds 50% limit. Suggested: Increase tenure to {suggested_tenure} months",
                    **updated_fields
                }
            )