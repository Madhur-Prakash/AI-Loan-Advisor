import requests
import time

BASE_URL = "http://localhost:8000"

def test_scenario_1_instant_approval():
    """Test Scenario 1: High credit score, instant approval"""
    print("\n🧪 Testing Scenario 1: Instant Approval (High Credit Score)")
    print("-" * 60)
    
    steps = [
        ("Hello", "Should ask for name"),
        ("My name is John Doe", "Should generate loan interest"),
        ("Yes, I'm interested in a loan", "Should ask for loan amount"),
        ("I need 3 lakh", "Should ask for tenure"),
        ("24 months", "Should show loan summary and ask for KYC"),
        ("My PAN is ABCDE1234F", "Should ask for Aadhar"),
        ("123456789012", "Should verify KYC and move to underwriting"),
        ("Continue", "Should show credit score and move to eligibility"),
        ("Continue", "Should approve instantly or ask for salary")
    ]
    
    app_id = None
    
    for i, (message, expected) in enumerate(steps, 1):
        print(f"\nStep {i}: {message}")
        print(f"Expected: {expected}")
        
        payload = {
            "customer_id": "TEST001",
            "message": message
        }
        
        if app_id:
            payload["application_id"] = app_id
            
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            app_id = data["application_id"]
            
            print(f"✅ Agent: {data['agent_name']}")
            print(f"📝 Response: {data['message'][:100]}...")
            print(f"📊 Status: {data['status']}")
            
            if data['status'] in ['approved', 'completed']:
                print("🎉 Loan approved! Continuing to PDF generation...")
                if data['status'] == 'approved':
                    # Trigger PDF generation
                    final_response = requests.post(f"{BASE_URL}/chat", json={
                        "customer_id": "TEST001",
                        "application_id": app_id,
                        "message": "Generate PDF"
                    })
                    if final_response.status_code == 200:
                        final_data = final_response.json()
                        print(f"📄 Final: {final_data['message'][:100]}...")
                break
            elif data['status'] == 'rejected':
                print("❌ Loan rejected")
                break
                
        else:
            print(f"❌ Error: {response.status_code}")
            break
            
        time.sleep(1)  # Small delay between requests
    
    return app_id

def test_scenario_2_salary_required():
    """Test Scenario 2: Conditional approval requiring salary"""
    print("\n🧪 Testing Scenario 2: Conditional Approval (Salary Required)")
    print("-" * 60)
    
    # Similar to scenario 1 but with different loan amount or credit score
    # This will trigger salary requirement
    
    steps = [
        ("Hello", "Should ask for name"),
        ("My name is Sarah Smith", "Should generate loan interest"),
        ("Yes, I need a loan", "Should ask for loan amount"),
        ("I need 8 lakh", "Should ask for tenure"),
        ("36 months", "Should show loan summary"),
        ("BCDEF5678G", "Should ask for Aadhar"),
        ("987654321098", "Should verify KYC"),
        ("Continue", "Should show credit assessment"),
        ("Continue", "Should ask for salary or approve"),
        ("My salary is 60000", "Should approve based on EMI ratio")
    ]
    
    app_id = None
    
    for i, (message, expected) in enumerate(steps, 1):
        print(f"\nStep {i}: {message}")
        
        payload = {
            "customer_id": "TEST002", 
            "message": message
        }
        
        if app_id:
            payload["application_id"] = app_id
            
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            app_id = data["application_id"]
            
            print(f"✅ Status: {data['status']} | Agent: {data['agent_name']}")
            print(f"📝 Response: {data['message'][:80]}...")
            
            if data['status'] in ['approved', 'completed', 'rejected']:
                break
                
        time.sleep(1)
    
    return app_id

def test_scenario_3_rejection():
    """Test Scenario 3: Rejection due to high EMI ratio"""
    print("\n🧪 Testing Scenario 3: Rejection (High EMI Ratio)")
    print("-" * 60)
    
    steps = [
        ("Hello", "Should ask for name"),
        ("My name is Mike Johnson", "Should generate loan interest"),
        ("I want a loan", "Should ask for loan amount"),
        ("I need 10 lakh", "Should ask for tenure"),
        ("24 months", "Should show loan summary"),
        ("CDEFG9012H", "Should ask for Aadhar"),
        ("456789012345", "Should verify KYC"),
        ("Continue", "Should show credit assessment"),
        ("Continue", "Should ask for salary"),
        ("My salary is 25000", "Should reject due to high EMI ratio")
    ]
    
    app_id = None
    
    for i, (message, expected) in enumerate(steps, 1):
        print(f"\nStep {i}: {message}")
        
        payload = {
            "customer_id": "TEST003",
            "message": message
        }
        
        if app_id:
            payload["application_id"] = app_id
            
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            app_id = data["application_id"]
            
            print(f"✅ Status: {data['status']} | Agent: {data['agent_name']}")
            print(f"📝 Response: {data['message'][:80]}...")
            
            if data['status'] == 'rejected':
                print("❌ Loan rejected as expected")
                break
            elif data['status'] in ['approved', 'completed']:
                print("⚠️ Unexpected approval")
                break
                
        time.sleep(1)
    
    return app_id

def run_all_scenarios():
    """Run all test scenarios"""
    print("🚀 Running All Test Scenarios")
    print("=" * 60)
    
    # Check server health
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return
    except:
        print("❌ Cannot connect to server. Start with: uv run python main.py")
        return
    
    # Run scenarios
    app1 = test_scenario_1_instant_approval()
    app2 = test_scenario_2_salary_required()
    app3 = test_scenario_3_rejection()
    
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"Scenario 1 (Instant Approval): {app1 or 'Failed'}")
    print(f"Scenario 2 (Conditional): {app2 or 'Failed'}")
    print(f"Scenario 3 (Rejection): {app3 or 'Failed'}")
    
    # Check generated PDFs
    if app1:
        pdf_response = requests.get(f"{BASE_URL}/sanction-letter/{app1}")
        if pdf_response.status_code == 200:
            print("✅ PDF generation working")
        else:
            print("❌ PDF generation failed")

if __name__ == "__main__":
    run_all_scenarios()