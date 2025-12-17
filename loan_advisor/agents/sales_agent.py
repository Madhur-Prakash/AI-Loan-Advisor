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
                    "It's completely okay to feel nervous or unsure — I'm here to help.\n"
                    "We can start with small, comfortable plans and adjust as you feel confident.\n\n"
                    f"Two gentle starting options:\n"
                    f"• Option A: ₹{amt1:,.0f} over {ten1} months → EMI ₹{emi1:,.0f} (10.5% p.a.)\n"
                    f"• Option B: ₹{amt2:,.0f} over {ten2} months → EMI ₹{emi2:,.0f} (10.5% p.a.)\n\n"
                    "If you prefer, tell me a comfortable monthly EMI (e.g., ₹5,000–₹10,000), "
                    "and I'll suggest an amount/tenure that fits. Otherwise, share any loan amount you're considering."
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
                    "I understand the hesitation — let's make this simple.\n"
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

            if application.loan_amount is not None and application.tenure_months:
                amt = application.loan_amount
                if amt <= 500000:
                    rate = 10.5
                elif amt <= 1000000:
                    rate = 11.5
                else:
                    rate = 12.5

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

        # Handle interest rate negotiation requests
        rate_negotiation_keywords = ["reduce", "lower", "decrease", "discount", "better rate", "negotiate", "can you do better", "best rate"]
        if any(keyword in ml for keyword in rate_negotiation_keywords):
            if application.loan_amount:
                current_rate = 10.5 if application.loan_amount <= 500000 else (11.5 if application.loan_amount <= 1000000 else 12.5)
                reduced_rate = max(9.5, current_rate - 0.5)  # Minimum 9.5%, reduce by 0.5%
                
                if application.tenure_months:
                    old_emi = self.calculate_emi(application.loan_amount, current_rate, application.tenure_months)
                    new_emi = self.calculate_emi(application.loan_amount, reduced_rate, application.tenure_months)
                    savings = old_emi - new_emi
                    
                    msg = (
                        f"🎯 **Great news!** I can offer you a special rate of {reduced_rate}% p.a.!\n\n"
                        f"💰 **Your Updated Plan:**\n"
                        f"• Loan Amount: ₹{application.loan_amount:,.0f}\n"
                        f"• New Rate: {reduced_rate}% p.a. (was {current_rate}%)\n"
                        f"• Tenure: {application.tenure_months} months\n"
                        f"• New EMI: ₹{new_emi:,.0f} (saves ₹{savings:,.0f}/month!)\n\n"
                        "This is our best rate for your profile! Ready to proceed?"
                    )
                    
                    return AgentResponse(
                        agent_name=self.name,
                        message=msg,
                        data_updates={"interest_rate": reduced_rate}
                    )
                else:
                    msg = (
                        f"🎯 **Excellent!** I can offer you a special rate of {reduced_rate}% p.a.!\n\n"
                        f"Let me show you the EMI options with this better rate for ₹{application.loan_amount:,.0f}:\n\n"
                    )
                    
                    tenures = [12, 24, 36, 48, 60]
                    emi_options = "\n".join([f"• **{t} months** → EMI ₹{self.calculate_emi(application.loan_amount, reduced_rate, t):,.0f}" for t in tenures])
                    
                    msg += f"{emi_options}\n\nWhich tenure works best for you?"
                    
                    return AgentResponse(
                        agent_name=self.name,
                        message=msg,
                        data_updates={"interest_rate": reduced_rate},
                        action_required="collect_tenure"
                    )
            else:
                msg = "I'd be happy to discuss better rates! First, let me know your desired loan amount."
                return AgentResponse(
                    agent_name=self.name,
                    message=msg,
                    action_required="collect_loan_amount"
                )

        # Extract loan amount from message if not already set
        if not application.loan_amount:
            # Look for amount patterns in the message
            amount_patterns = [
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lakhs)',
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|crores)',
                r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees?',
                r'\b(\d{4,})\b'  # 4+ digit numbers as potential amounts
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, ml)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        if 'lakh' in ml:
                            amount *= 100000
                        elif 'crore' in ml:
                            amount *= 10000000
                        
                        # Only accept reasonable loan amounts
                        if 10000 <= amount <= 50000000:
                            application.loan_amount = amount
                            break
                    except ValueError:
                        continue

        # Only extract tenure if explicitly mentioned with units, not bare numbers
        if not application.tenure_months:
            tmatch = re.search(r"(\d+)\s*(months?|month|yrs?|years?|y)\b", ml)
            if tmatch:
                tval = int(tmatch.group(1))
                unit = tmatch.group(2)
                if unit.startswith("y") or unit.startswith("yr") or unit.startswith("year"):
                    tval *= 12
                application.tenure_months = tval

        if ("interest" in ml or "rate" in ml):
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

        if any(t in ml for t in ["repayment", "repay", "plan", "plans", "schedule", "installment", "emi options", "tenure options"]):
            if application.loan_amount is not None:
                msg = (
                    "Here's how repayment works at SYNFIN:\n"
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
            msg = (
                "Perfect! I'm here to help you find the best loan option. \n\n"
                "To get started, what loan amount are you considering? \n"
                "💡 **Popular choices:**\n"
                "• ₹2,00,000 - ₹5,00,000 (10.5% interest)\n"
                "• ₹5,00,000 - ₹10,00,000 (11.5% interest)\n"
                "• Above ₹10,00,000 (12.5% interest)\n\n"
                "Feel free to share any amount that works for your needs!"
            )
            return AgentResponse(
                agent_name=self.name,
                message=msg,
                action_required="collect_loan_amount"
            )
        
        # Show EMI options when loan amount is available but tenure is not
        if application.loan_amount and not application.tenure_months:
            amt = application.loan_amount
            if amt <= 500000:
                rate = 10.5
                rate_benefit = "Excellent! You qualify for our lowest rate of 10.5% 🎉"
            elif amt <= 1000000:
                rate = 11.5
                rate_benefit = "Great choice! Your rate is 11.5% - very competitive! 💪"
            else:
                rate = 12.5
                rate_benefit = "Perfect! For higher amounts, your rate is 12.5% 🚀"
            
            tenures = [12, 24, 36, 48, 60]
            emi_options = "\n".join([f"• **{t} months** → EMI ₹{self.calculate_emi(amt, rate, t):,.0f}" for t in tenures])
            
            total_12 = self.calculate_emi(amt, rate, 12) * 12
            total_60 = self.calculate_emi(amt, rate, 60) * 60
            savings = total_60 - total_12
            
            msg = (
                f"{rate_benefit}\n\n"
                f"💰 **Loan Amount:** ₹{amt:,.0f}\n"
                f"📈 **Interest Rate:** {rate}% p.a.\n\n"
                f"📅 **Choose your comfortable EMI:**\n"
                f"{emi_options}\n\n"
                f"💡 **Smart Tip:** Shorter tenure saves you ₹{savings:,.0f} in total interest!\n"
                f"But longer tenure gives lower EMI for better cash flow.\n\n"
                "Which tenure feels right for your budget? I can also suggest a custom tenure!"
            )
            return AgentResponse(
                agent_name=self.name,
                message=msg,
                action_required="collect_tenure"
            )
        
        # Final calculation when both amount and tenure are available
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
        
        total_interest = (emi * application.tenure_months) - application.loan_amount
        total_payable = emi * application.tenure_months
        
        alt_tenure_short = max(12, application.tenure_months - 12)
        alt_tenure_long = min(60, application.tenure_months + 12)
        alt_emi_short = self.calculate_emi(application.loan_amount, interest_rate, alt_tenure_short)
        alt_emi_long = self.calculate_emi(application.loan_amount, interest_rate, alt_tenure_long)
        
        summary_msg = (
            f"🎉 **Perfect! Here's your personalized loan plan:**\n\n"
            f"💰 **Loan Amount:** ₹{application.loan_amount:,.0f}\n"
            f"📈 **Interest Rate:** {interest_rate}% p.a. (Competitive rate!)\n"
            f"📅 **Tenure:** {application.tenure_months} months\n"
            f"💳 **Monthly EMI:** ₹{emi:,.0f}\n"
            f"📊 **Total Interest:** ₹{total_interest:,.0f}\n"
            f"💵 **Total Payable:** ₹{total_payable:,.0f}\n\n"
            f"💡 **Want to explore other options?**\n"
            f"• **{alt_tenure_short} months:** EMI ₹{alt_emi_short:,.0f} (Save on interest!)\n"
            f"• **{alt_tenure_long} months:** EMI ₹{alt_emi_long:,.0f} (Lower EMI!)\n\n"
            "**Ready to proceed?** Say 'proceed' for KYC verification, or let me know if you'd like to adjust anything! 🚀"
        )

        return AgentResponse(
            agent_name=self.name,
            message=summary_msg,
            data_updates={
                "interest_rate": interest_rate,
                "emi": emi,
                "status": LoanStatus.SALES_DISCUSSION.value
            }
        )
