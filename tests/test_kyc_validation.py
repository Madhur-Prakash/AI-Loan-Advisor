import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'loan_advisor')))
from loan_advisor.agents.verification_agent import VerificationAgent
from loan_advisor.models.loan_models import LoanApplication, Customer


async def run_case(description: str, pan: str, aadhar: str):
    agent = VerificationAgent()
    app = LoanApplication(
        application_id="TEST_KYC",
        customer=Customer(customer_id="TEST_CUST", name="Test User", pan=pan, aadhar=aadhar),
        status="kyc_verification",
    )

    resp = await agent.process(app, "")
    print(f"\n=== {description} ===")
    print(f"Agent: {resp.agent_name}")
    print(f"Message: {resp.message}")
    if resp.data_updates:
        print(f"Data Updates: {resp.data_updates}")
    return resp


async def main():
    # Case 1: Invalid PAN, valid Aadhar
    resp1 = await run_case(
        "Invalid PAN format",
        pan="ABCD1234F",  # invalid (only 4 letters before digits)
        aadhar="123456789012",  # valid
    )
    assert "Invalid PAN format" in resp1.message
    assert resp1.data_updates and resp1.data_updates.get("rejection_reason") == "Invalid PAN format"

    # Case 2: Valid PAN, Invalid Aadhar
    resp2 = await run_case(
        "Invalid Aadhar format",
        pan="ABCDE1234F",  # valid
        aadhar="12345678",  # invalid (not 12 digits)
    )
    assert "Invalid Aadhar format" in resp2.message
    assert resp2.data_updates and resp2.data_updates.get("rejection_reason") == "Invalid Aadhar format"

    # Case 3: Both PAN and Aadhar invalid
    resp3 = await run_case(
        "Both PAN and Aadhar invalid",
        pan="ABCD1234F",  # invalid
        aadhar="12345678",  # invalid
    )
    # Aggregated validation should report both errors
    assert "Invalid PAN format" in resp3.message
    assert "Invalid Aadhar format" in resp3.message
    assert resp3.data_updates
    assert "Invalid PAN format" in resp3.data_updates.get("rejection_reason", "")
    assert "Invalid Aadhar format" in resp3.data_updates.get("rejection_reason", "")

    print("\n✅ KYC validation tests passed.")


if __name__ == "__main__":
    asyncio.run(main())