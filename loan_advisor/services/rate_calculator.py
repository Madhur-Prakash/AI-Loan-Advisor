"""Dynamic interest rate calculator for SYNFIN loans"""

class RateCalculator:
    """Calculate dynamic interest rates based on loan parameters"""
    
    # Base rates and risk premiums
    BASE_RATE = 9.0  # Base lending rate
    RISK_FREE_RATE = 6.5  # Government bond rate
    
    def calculate_rate(self, loan_amount: float, tenure_months: int = 36, credit_score: int = None) -> float:
        """
        Calculate dynamic interest rate based on:
        - Loan amount (higher amounts = better rates due to economies of scale)
        - Tenure (longer tenure = slightly higher rate due to time risk)
        - Credit score (if available, better score = better rate)
        """
        
        # Start with base rate
        rate = self.BASE_RATE
        
        # Amount-based adjustment (volume discount)
        if loan_amount <= 500000:  # Up to 5 lakhs
            amount_premium = 1.5
        elif loan_amount <= 1000000:  # 5-10 lakhs
            amount_premium = 1.2
        elif loan_amount <= 2500000:  # 10-25 lakhs
            amount_premium = 1.0
        elif loan_amount <= 5000000:  # 25-50 lakhs
            amount_premium = 0.8
        elif loan_amount <= 10000000:  # 50 lakhs - 1 crore
            amount_premium = 0.6
        else:  # Above 1 crore (bulk discount)
            amount_premium = 0.4
        
        # Tenure-based adjustment (time risk)
        if tenure_months <= 12:
            tenure_premium = 0.0
        elif tenure_months <= 24:
            tenure_premium = 0.3
        elif tenure_months <= 36:
            tenure_premium = 0.5
        elif tenure_months <= 48:
            tenure_premium = 0.7
        else:  # 48-60 months
            tenure_premium = 1.0
        
        # Credit score adjustment (if available)
        credit_premium = 0.0
        if credit_score:
            if credit_score >= 800:
                credit_premium = -0.5  # Excellent credit discount
            elif credit_score >= 750:
                credit_premium = 0.0  # Good credit
            elif credit_score >= 700:
                credit_premium = 0.3  # Fair credit
            elif credit_score >= 650:
                credit_premium = 0.8  # Below average
            else:
                credit_premium = 1.5  # Poor credit
        
        # Calculate final rate
        final_rate = rate + amount_premium + tenure_premium + credit_premium
        
        # Ensure rate is within reasonable bounds (9.5% - 15%)
        final_rate = max(9.5, min(15.0, final_rate))
        
        # Round to nearest 0.5%
        final_rate = round(final_rate * 2) / 2
        
        return final_rate
    
    def get_negotiated_rate(self, current_rate: float, loan_amount: float) -> float:
        """
        Calculate negotiated rate (typically 0.5-1% reduction)
        Larger loans get better negotiation discounts
        """
        if loan_amount >= 5000000:  # 50 lakhs+
            discount = 1.0
        elif loan_amount >= 2000000:  # 20 lakhs+
            discount = 0.75
        else:
            discount = 0.5
        
        negotiated_rate = current_rate - discount
        
        # Minimum rate floor (9.5%)
        return max(9.5, negotiated_rate)
    
    def get_rate_breakdown(self, loan_amount: float, tenure_months: int = 36, credit_score: int = None) -> dict:
        """Get detailed breakdown of rate calculation"""
        rate = self.calculate_rate(loan_amount, tenure_months, credit_score)
        
        return {
            "final_rate": rate,
            "base_rate": self.BASE_RATE,
            "loan_amount": loan_amount,
            "tenure_months": tenure_months,
            "credit_score": credit_score,
            "benefits": self._get_rate_benefits(loan_amount, tenure_months)
        }
    
    def _get_rate_benefits(self, loan_amount: float, tenure_months: int) -> str:
        """Generate user-friendly explanation of rate benefits"""
        benefits = []
        
        if loan_amount >= 5000000:
            benefits.append(" Premium customer discount applied!")
        elif loan_amount >= 2000000:
            benefits.append(" High-value loan discount!")
        elif loan_amount >= 1000000:
            benefits.append(" Volume discount applied!")
        
        if tenure_months <= 24:
            benefits.append(" Short tenure bonus!")
        
        return " ".join(benefits) if benefits else "Competitive market rate"
