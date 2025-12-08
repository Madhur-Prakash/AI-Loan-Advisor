import asyncio
import json
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.agents.pdf_agent import PDFAgent
from loan_advisor.models.loan_models import LoanApplication, Customer, LoanStatus

load_dotenv()

async def generate_sample():
    app = LoanApplication(
        application_id="SAMPLE_001",
        customer=Customer(
            customer_id='CUST001',
            name='John Doe',
            email='test@example.com',
            pan='ABCDE1234F',
            aadhar='123456789012',
            credit_score=750
        ),
        loan_amount=500000,
        interest_rate=10.5,
        tenure_months=36,
        emi=16134.00,
        pre_approved_limit=800000,
        status=LoanStatus.APPROVED
    )
    
    pdf_agent = PDFAgent()
    
    # Generate the PDF without sending email (pass empty message)
    pdf_result = pdf_agent._generate_sanction_letter(app)
    appwrite_file = pdf_result["appwrite_file"]
    
    # Construct public URL
    bucket_id = os.getenv("BUCKET_ID")
    api_endpoint = os.getenv("API_ENDPOINT")
    project_id = os.getenv("PROJECT_ID")
    file_id = appwrite_file['$id']
    
    public_url = f"{api_endpoint}/storage/buckets/{bucket_id}/files/{file_id}/view?project={project_id}"
    
    print("\n" + "="*60)
    print("SAMPLE PDF GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"File ID: {file_id}")
    print(f"Filename: {pdf_result['filename']}")
    print(f"\nPublic URL:")
    print(public_url)
    print("="*60)
    
    return {
        "file_id": file_id,
        "public_url": public_url,
        "filename": pdf_result['filename'],
        "appwrite_file": appwrite_file
    }

if __name__ == "__main__":
    result = asyncio.run(generate_sample())
    print(f"\n✅ Use this URL for testing: {result['public_url']}")