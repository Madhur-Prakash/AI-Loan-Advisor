import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from loan_advisor.agents.master_agent import MasterAgent
from loan_advisor.models.loan_models import LoanApplication, Customer, LoanStatus

async def test_llm_integration():
    print("Testing LLM Integration")
    
    # Check if API key is set
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        print("WARNING: GROQ_API_KEY not set. Using fallback responses.")
        print("To use actual LLM, set your Groq API key in .env file")
    
    # Create test application
    app = LoanApplication(
        application_id="TEST_001",
        customer=Customer(customer_id="CUST001"),
        status=LoanStatus.INITIATED
    )
    
    # Test Master Agent
    master_agent = MasterAgent()
    response = await master_agent.process(app, "Hello")
    
    print(f"\nMaster Agent Response:")
    print(f"Agent: {response.agent_name}")
    print(f"Message: {response.message}")
    print(f"Action Required: {response.action_required}")
    
    # Test with name provided
    app.customer.name = "John Doe"
    response2 = await master_agent.process(app, "I'm interested in a loan")
    
    print(f"\nMaster Agent Response (with name):")
    print(f"Agent: {response2.agent_name}")
    print(f"Message: {response2.message}")
    print(f"Next Agent: {response2.next_agent}")

if __name__ == "__main__":
    asyncio.run(test_llm_integration())