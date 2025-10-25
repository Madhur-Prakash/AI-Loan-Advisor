import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.agents.pdf_agent import PDFAgent
from loan_advisor.models.loan_models import LoanApplication, Customer, LoanStatus

async def generate_sample():
    app = LoanApplication(
        application_id="SAMPLE_001",
        customer=Customer(
            customer_id='CUST001',
            name='John Doe',
            pan='ABCDE1234F',
            credit_score=750
        ),
        loan_amount=500000,
        interest_rate=10.5,
        tenure_months=24,
        emi=23456.78,
        status=LoanStatus.APPROVED
    )
    
    pdf_agent = PDFAgent()
    result = await pdf_agent.process(app, '')
    print(f"Sample sanction letter generated: {result.data_updates['sanction_letter_path']}")

if __name__ == "__main__":
    asyncio.run(generate_sample())