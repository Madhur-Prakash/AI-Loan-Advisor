import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from agents.base_agent import BaseAgent
from models.loan_models import LoanApplication, AgentResponse, LoanStatus

class PDFAgent(BaseAgent):
    def __init__(self):
        super().__init__("PDF Agent")
        os.makedirs("sanction_letters", exist_ok=True)
    
    async def process(self, application: LoanApplication, message: str) -> AgentResponse:
        pdf_path = self._generate_sanction_letter(application)
        
        return AgentResponse(
            agent_name=self.name,
            message=f"🎉 Your loan has been approved! Your sanction letter has been generated.\n"
                   f"Document: {pdf_path}\n\n"
                   f"Thank you for choosing our services. Have a great day!",
            data_updates={
                "status": LoanStatus.COMPLETED.value,
                "sanction_letter_path": pdf_path
            }
        )
    
    def _generate_sanction_letter(self, application: LoanApplication) -> str:
        filename = f"sanction_letters/sanction_letter_{application.application_id}.pdf"
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "LOAN SANCTION LETTER")
        
        # Date
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        # Customer details
        y_pos = height - 150
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "Customer Details:")
        
        y_pos -= 30
        c.setFont("Helvetica", 12)
        details = [
            f"Name: {application.customer.name}",
            f"Application ID: {application.application_id}",
            f"PAN: {application.customer.pan}",
            f"Credit Score: {application.customer.credit_score}"
        ]
        
        for detail in details:
            c.drawString(70, y_pos, detail)
            y_pos -= 20
        
        # Loan details
        y_pos -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "Loan Details:")
        
        y_pos -= 30
        c.setFont("Helvetica", 12)
        loan_details = [
            f"Loan Amount: ₹{application.loan_amount:,.0f}",
            f"Interest Rate: {application.interest_rate}% per annum",
            f"Tenure: {application.tenure_months} months",
            f"EMI: ₹{application.emi:,.0f}",
            f"Total Amount Payable: ₹{application.emi * application.tenure_months:,.0f}"
        ]
        
        for detail in loan_details:
            c.drawString(70, y_pos, detail)
            y_pos -= 20
        
        # Terms
        y_pos -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "Terms & Conditions:")
        
        y_pos -= 30
        c.setFont("Helvetica", 10)
        terms = [
            "• This sanction is valid for 30 days from the date of issue",
            "• Processing fee: 2% of loan amount (minimum ₹1,000)",
            "• First EMI due date: 30 days from disbursement",
            "• Prepayment allowed after 6 months with 2% charges"
        ]
        
        for term in terms:
            c.drawString(70, y_pos, term)
            y_pos -= 15
        
        # Footer
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 100, "Congratulations on your loan approval!")
        c.setFont("Helvetica", 10)
        c.drawString(50, 80, "For any queries, contact us at support@loancompany.com")
        
        c.save()
        return filename