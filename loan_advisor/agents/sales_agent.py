from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus
import re

class SalesAgent(BaseAgent):
    def __init__(self):
        super().__init__("FINA (Financial Interaction & Negotiation Assistant)")
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        context = self.get_context(application)
        ml = (message or "").lower()

        # Handle uncertainty/hesitation intent empathetically to ease the user
        # Expand detection to include more variants and explicit tenure ambiguity like "X or Y years"
        base_tokens = [
            "unsure", "not sure", "nervous", "confused", "uncertain", "hesitant", "anxious",
            "doubt", "dilemma", "overwhelmed", "worried", "maybe", "perhaps", "not confident"
        ]
        regex_patterns = [
            r"\bconfus(?:e|ed|ion)\b",
            r"\bmaybe\b",
            r"\bperhaps\b",
            r"\bnot\s+confident\b",
            r"\b(?:can\'t|cannot)\s+(?:decide|choose)\b",
            r"\bnot\s+sure\b",
            r"\bunsure\b",
            r"\bdilemma\b",
            r"\boverwhelmed\b",
            r"\bworried\b",
            r"\bhesitant\b",
            r"\banxious\b",
        ]
        ambiguous_tenure = re.search(r"\b(\d+)\s*(months?|years?)\b.*\bor\b.*\b(\d+)\s*(months?|years?)\b", ml)
        uncertainty_intent = (
            any(p in ml for p in base_tokens)
            or any(re.search(pat, ml) for pat in regex_patterns)
            or bool(ambiguous_tenure)
        )

        if uncertainty_intent:
            if application.loan_amount is None:
                rate = 10.5
                amt1, ten1 = 200000, 36
                amt2, ten2 = 300000, 48
                emi1 = self.calculate_emi(amt1, rate, ten1)
                emi2 = self.calculate_emi(amt2, rate, ten2)
                msg = (
                    "It’s completely okay to feel nervous or unsure — I’m here to help.\n"
                    "We can start with small, comfortable plans and adjust as you feel confident.\n\n"
                    f"Two gentle starting options:\n"
                    f"• Option A: ₹{amt1:,.0f} over {ten1} months → EMI ₹{emi1:,.0f} (10.5% p.a.)\n"
                    f"• Option B: ₹{amt2:,.0f} over {ten2} months → EMI ₹{emi2:,.0f} (10.5% p.a.)\n\n"
                    "If you prefer, tell me a comfortable monthly EMI (e.g., ₹5,000–₹10,000), "
                    "and I’ll suggest an amount/tenure that fits. Otherwise, share any loan amount you’re considering."
                )
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_loan_amount"
                )

            if application.loan_amount is not None and not application.tenure_months:
                amt = application.loan_amount
                if amt <= 500000:
                    rate = 10.5
                elif amt <= 1000000:
                    rate = 11.5
                else:
                    rate = 12.5
                tchoices = [24, 36, 60]
                emis = {t: self.calculate_emi(amt, rate, t) for t in tchoices}
                msg = (
                    "I understand the hesitation — let’s make this simple.\n"
                    f"For ₹{amt:,.0f} at {rate}% p.a., here are illustrative EMIs by tenure:\n"
                    f"• {tchoices[0]} months → EMI ₹{emis[tchoices[0]]:,.0f}\n"
                    f"• {tchoices[1]} months → EMI ₹{emis[tchoices[1]]:,.0f}\n"
                    f"• {tchoices[2]} months → EMI ₹{emis[tchoices[2]]:,.0f}\n\n"
                    "Longer tenure lowers EMI but increases total interest. Which tenure feels comfortable to you?"
                )
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_tenure"
                )

            # If the user expresses uncertainty but a tenure is already set (possibly auto-parsed),
            # avoid summarizing and instead offer clear comparisons to help decide.
            if application.loan_amount is not None and application.tenure_months:
                amt = application.loan_amount
                # Determine rate slab
                if amt <= 500000:
                    rate = 10.5
                elif amt <= 1000000:
                    rate = 11.5
                else:
                    rate = 12.5

                # Prefer comparing explicitly mentioned ambiguous tenures like "X or Y years"
                m = ambiguous_tenure
                if m:
                    try:
                        n1 = int(m.group(1)); u1 = (m.group(2) or "")
                        n2 = int(m.group(3)); u2 = (m.group(4) or "")
                        t1 = n1 * 12 if (u1.startswith("y")) else n1
                        t2 = n2 * 12 if (u2.startswith("y")) else n2
                        e1 = self.calculate_emi(amt, rate, t1)
                        e2 = self.calculate_emi(amt, rate, t2)
                        msg = (
                            f"You mentioned {t1} months versus {t2} months. For ₹{amt:,.0f} at {rate}% p.a.:\n"
                            f"• {t1} months → EMI ₹{e1:,.0f}\n"
                            f"• {t2} months → EMI ₹{e2:,.0f}\n\n"
                            "Longer tenure lowers EMI but increases total interest. Which tenure feels comfortable to you?"
                        )
                        return AgentResponse(
                            agent_name=self.name,
                            message=msg,
                            action_required="collect_tenure"
                        )
                    except Exception:
                        pass

                # Otherwise, compare nearby options around the currently set tenure
                base_t = int(application.tenure_months)
                choices = sorted(set([max(12, base_t - 12), base_t, min(120, base_t + 12)]))
                emis = {t: self.calculate_emi(amt, rate, t) for t in choices}
                comp_lines = "\n".join([f"• {t} months → EMI ₹{emis[t]:,.0f}" for t in choices])
                msg = (
                    f"Here are nearby tenure options for ₹{amt:,.0f} at {rate}% p.a.:\n"
                    f"{comp_lines}\n\n"
                    "Longer tenure lowers EMI but increases total interest. Which tenure feels comfortable to you?"
                )
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_tenure"
                )


        # Lightweight tenure parsing as a fallback (or reinforcement) to orchestrator extraction
        # Handles phrases like "for 40 months" or "40 months"
        if not application.tenure_months:
            # Case A: explicit unit provided
            tmatch = re.search(r"(\d+)\s*(months?|month|yrs?|years?|y)\b", ml)
            if tmatch:
                tval = int(tmatch.group(1))
                unit = tmatch.group(2)
                if unit.startswith("y") or unit.startswith("yr") or unit.startswith("year"):
                    tval *= 12
                application.tenure_months = tval
            else:
                # Case B: bare number that looks like tenure (6–120)
                bare = re.search(r"\b(\d{1,3})\b", ml)
                if bare:
                    num = int(bare.group(1))
                    if 6 <= num <= 120:
                        application.tenure_months = num

        # If user asks about interest/rates at any point, respond with slabs immediately.
        # Do not move to KYC here; instead, ask for tenure to proceed to EMI.
        if ("interest" in ml or "rate" in ml):
            # Determine rate slab based on known loan amount, if available
            if application.loan_amount is not None:
                if application.loan_amount <= 500000:
                    slab = 10.5
                    slab_text = "Up to ₹5,00,000: 10.5% p.a."
                elif application.loan_amount <= 1000000:
                    slab = 11.5
                    slab_text = "₹5,00,001–₹10,00,000: 11.5% p.a."
                else:
                    slab = 12.5
                    slab_text = "> ₹10,00,000: 12.5% p.a."
                msg = (
                    f"Here are SYNFIN's interest rates by amount:\n"
                    f"- {slab_text}\n\n"
                    f"Given your amount of ₹{application.loan_amount:,.0f}, the working rate is {slab}% p.a.\n"
                    f"To compute your EMI, please share preferred tenure (12–60 months)."
                )
            else:
                msg = (
                    "SYNFIN interest rate slabs:\n"
                    "- Up to ₹5,00,000: 10.5% p.a.\n"
                    "- ₹5,00,001–₹10,00,000: 11.5% p.a.\n"
                    "> ₹10,00,000: 12.5% p.a.\n\n"
                    "Please share your desired loan amount and tenure (12–60 months) to calculate EMI."
                )
            return AgentResponse(
                agent_name=self.name,
                message=msg,
                action_required="collect_tenure" if application.loan_amount else "collect_loan_amount"
            )

        # If user asks about repayment plans/options/schedule, explain tenure and EMI behavior.
        if any(t in ml for t in ["repayment", "repay", "plan", "plans", "schedule", "installment", "emi options", "tenure options"]):
            if application.loan_amount is not None:
                msg = (
                    "Here’s how repayment works at SYNFIN:\n"
                    "- Tenure: 12–60 months. Longer tenure → lower EMI, higher total interest.\n"
                    "- EMI: Fixed monthly installment calculated from amount, tenure, and rate slab.\n"
                    "- Prepayment: Allowed; making extra payments reduces interest over time.\n"
                    "- Foreclosure: You can close the loan early; charges depend on plan.\n\n"
                    "To personalise this, please share your preferred tenure (12–60 months) so I can compute the EMI for ₹"
                    f"{application.loan_amount:,.0f}."
                )
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_tenure"
                )
            else:
                msg = (
                    "We offer flexible repayment plans with tenures from 12 to 60 months.\n"
                    "EMI is determined by loan amount, tenure, and interest slab.\n\n"
                    "Please share your desired loan amount and a tentative tenure to illustrate EMI options."
                )
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_loan_amount"
                )
        
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
        
        # Deterministic summary so we don't re-ask for tenure when it's present
        summary_msg = (
            "Here’s your loan summary:\n"
            f"- Amount: ₹{application.loan_amount:,.0f}\n"
            f"- Interest Rate: {interest_rate}% p.a.\n"
            f"- Tenure: {application.tenure_months} months\n"
            f"- EMI: ₹{emi:,.0f}\n\n"
            "Would you like to proceed to KYC verification now, or adjust the amount/tenure?"
        )

        # Do NOT auto-switch to verification here. Let the user confirm or provide PAN/Aadhar.
        return AgentResponse(
            agent_name=self.name,
            message=summary_msg,
            data_updates={
                "interest_rate": interest_rate,
                "emi": emi,
                # Keep status in Sales until user signals KYC (PAN/Aadhar or explicit 'kyc')
                "status": LoanStatus.SALES_DISCUSSION.value
            }
        )