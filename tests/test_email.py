import os
import sys
import argparse
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.services.gen_email import generate_email, convert_string_to_json
from loan_advisor.services.send_email import send_email_with_url_attachment

load_dotenv()

def run_test_case(case_name: str, to_email: str):
    """Run a specific test case"""
    test_cases = {
        "approval": test_instant_approval,
        "conditional": test_conditional_approval,
        "rejection": test_rejection
    }
    
    if case_name == "all":
        for name, func in test_cases.items():
            func(to_email)
    elif case_name in test_cases:
        test_cases[case_name](to_email)
    else:
        print(f"❌ Unknown test case: {case_name}")
        print(f"Available: {', '.join(test_cases.keys())}, all")

def test_instant_approval(to_email: str):
    print("\n" + "="*60)
    print("TEST CASE: INSTANT APPROVAL WITH PDF ATTACHMENT")
    print("="*60)
    approval_context = (
        "Loan Application Approved for John Doe. "
        "Loan Amount: ₹500,000, "
        "EMI: ₹16,134, "
        "Tenure: 36 months, "
        "Interest Rate: 10.5% p.a., "
        "Credit Score: 750, "
        "Pre-approved Limit: ₹800,000. "
        "Status: APPROVED. Sanction letter attached."
    )
    
    # Sample Appwrite public URL (replace with actual URL from your Appwrite storage)
    sample_pdf_url = "https://fra.cloud.appwrite.io/v1/storage/buckets/6856b5e8002828b1fe22/files/7e7bece4-25b5-45af-9756-f6bf64333169/view?project=6856b323003243cb7206"
    
    email_json_str = generate_email(to_email, approval_context)
    email_data = convert_string_to_json(email_json_str)
    
    if email_data:
        print(f"\nGenerated Email:")
        print(f"To: {email_data['recipient_email']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Body Preview: {email_data['body'][:200]}...")
        print(f"PDF URL: {sample_pdf_url}")
        
        # Note: This will fail if the file doesn't exist in Appwrite
        # For testing, you can use a real file ID from your Appwrite storage
        try:
            send_email_with_url_attachment(
                email_data["recipient_email"], 
                email_data["subject"], 
                email_data["body"],
                sample_pdf_url
            )
            print("✅ Instant Approval email with PDF sent successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send email with attachment: {e}")
            print("Note: Make sure the PDF file exists in Appwrite storage or use a valid file URL")

def test_conditional_approval(to_email: str):
    print("\n" + "="*60)
    print("TEST CASE: CONDITIONAL APPROVAL WITH PDF ATTACHMENT")
    print("="*60)
    conditional_context = (
        "Loan Application Approved for Jane Smith. "
        "Loan Amount: ₹1,200,000, "
        "EMI: ₹35,500, "
        "Tenure: 48 months, "
        "Interest Rate: 11.5% p.a., "
        "Monthly Salary: ₹80,000, "
        "EMI-to-Salary Ratio: 44.4%, "
        "Credit Score: 680. "
        "Status: APPROVED. Sanction letter attached."
    )
    
    sample_pdf_url = f"{os.getenv('API_ENDPOINT')}/storage/buckets/{os.getenv('BUCKET_ID')}/files/sample-file-id/view?project={os.getenv('PROJECT_ID')}"
    
    email_json_str = generate_email(to_email, conditional_context)
    email_data = convert_string_to_json(email_json_str)
    
    if email_data:
        print(f"\nGenerated Email:")
        print(f"To: {email_data['recipient_email']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Body Preview: {email_data['body'][:200]}...")
        print(f"PDF URL: {sample_pdf_url}")
        
        try:
            send_email_with_url_attachment(
                email_data["recipient_email"], 
                email_data["subject"], 
                email_data["body"],
                sample_pdf_url
            )
            print("✅ Conditional Approval email with PDF sent successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send email with attachment: {e}")
            print("Note: Make sure the PDF file exists in Appwrite storage or use a valid file URL")

def test_rejection(to_email: str):
    print("\n" + "="*60)
    print("TEST CASE: REJECTION WITH SUGGESTIONS (NO ATTACHMENT)")
    print("="*60)
    rejection_context = (
        "Loan Application Rejected for Mike Johnson. "
        "Loan Amount: ₹800,000, "
        "EMI: ₹28,500, "
        "Tenure: 36 months, "
        "Monthly Salary: ₹45,000, "
        "EMI-to-Salary Ratio: 63.3% (exceeds 50% limit). "
        "Rejection Reason: EMI-to-salary ratio too high. "
        "Suggestions: Try increasing tenure to 60 months. Estimated EMI: ₹18,200 (≤ 50% salary). "
        "Consider reducing loan amount to around ₹400,000 for current tenure. "
        "Make a higher down payment to reduce principal."
    )
    
    email_json_str = generate_email(to_email, rejection_context)
    email_data = convert_string_to_json(email_json_str)
    
    if email_data:
        print(f"\nGenerated Email:")
        print(f"To: {email_data['recipient_email']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Body Preview: {email_data['body'][:200]}...")
        
        # Rejection emails don't include PDF attachments
        # Using basic send_email (not implemented in current code, so skip)
        print("⚠️ Rejection emails are sent without attachments (feature not implemented in this test)")
        print("✅ Rejection email test completed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test email generation and sending for loan application")
    parser.add_argument(
        "--case",
        type=str,
        default="all",
        choices=["approval", "conditional", "rejection", "all"],
        help="Test case to run: approval, conditional, rejection, or all (default: all)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Recipient email (overrides TEST_EMAIL_RECIPIENT from .env)"
    )
    parser.add_argument(
        "--pdf-url",
        type=str,
        help="Custom PDF URL from Appwrite storage (optional, uses sample URL if not provided)"
    )
    
    args = parser.parse_args()
    to_email = args.email or os.getenv("TEST_EMAIL_RECIPIENT")
    
    if not to_email:
        print("❌ Error: No recipient email provided. Use --email or set TEST_EMAIL_RECIPIENT in .env")
        sys.exit(1)
    
    # Validate Appwrite configuration
    if not os.getenv('API_ENDPOINT') or not os.getenv('BUCKET_ID') or not os.getenv('PROJECT_ID'):
        print("⚠️ Warning: Appwrite configuration incomplete. Set API_ENDPOINT, BUCKET_ID, and PROJECT_ID in .env")
        print("Email with attachment tests may fail.\n")
    
    print(f"\n📧 Sending test emails to: {to_email}")
    if args.pdf_url:
        print(f"📎 Using custom PDF URL: {args.pdf_url}")
    run_test_case(args.case, to_email)
    
    print("\n" + "="*60)
    print("EMAIL TESTS COMPLETED")
    print("="*60)