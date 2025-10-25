import requests
import json

BASE_URL = "http://localhost:8000"

def test_loan_workflow():
    print("🚀 Testing AI Loan Processing Workflow\n")
    
    # Test 1: Start conversation
    print("1. Starting conversation...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "customer_id": "CUST001",
        "message": "Hello"
    })
    
    if response.status_code == 200:
        data = response.json()
        app_id = data["application_id"]
        print(f"✅ Agent: {data['agent_name']}")
        print(f"📝 Message: {data['message']}\n")
        
        # Test 2: Provide name
        print("2. Providing name...")
        response = requests.post(f"{BASE_URL}/chat", json={
            "customer_id": "CUST001",
            "application_id": app_id,
            "message": "My name is John Doe"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent: {data['agent_name']}")
            print(f"📝 Message: {data['message']}\n")
            
            # Test 3: Express interest in loan
            print("3. Expressing interest in loan...")
            response = requests.post(f"{BASE_URL}/chat", json={
                "customer_id": "CUST001",
                "application_id": app_id,
                "message": "Yes, I'm interested in a personal loan"
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Agent: {data['agent_name']}")
                print(f"📝 Message: {data['message']}\n")
                
                # Test 4: Provide loan amount
                print("4. Providing loan amount...")
                response = requests.post(f"{BASE_URL}/chat", json={
                    "customer_id": "CUST001",
                    "application_id": app_id,
                    "message": "I need 5 lakh rupees"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Agent: {data['agent_name']}")
                    print(f"📝 Message: {data['message']}\n")
                    
                    # Test 5: Provide tenure
                    print("5. Providing tenure...")
                    response = requests.post(f"{BASE_URL}/chat", json={
                        "customer_id": "CUST001",
                        "application_id": app_id,
                        "message": "24 months"
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Agent: {data['agent_name']}")
                        print(f"📝 Message: {data['message']}\n")
                        
                        # Test 6: Provide PAN
                        print("6. Providing PAN...")
                        response = requests.post(f"{BASE_URL}/chat", json={
                            "customer_id": "CUST001",
                            "application_id": app_id,
                            "message": "ABCDE1234F"
                        })
                        
                        if response.status_code == 200:
                            data = response.json()
                            print(f"✅ Agent: {data['agent_name']}")
                            print(f"📝 Message: {data['message']}\n")
                            
                            # Test 7: Provide Aadhar
                            print("7. Providing Aadhar...")
                            response = requests.post(f"{BASE_URL}/chat", json={
                                "customer_id": "CUST001",
                                "application_id": app_id,
                                "message": "123456789012"
                            })
                            
                            if response.status_code == 200:
                                data = response.json()
                                print(f"✅ Agent: {data['agent_name']}")
                                print(f"📝 Message: {data['message']}\n")
                                
                                # Continue the workflow automatically
                                print("8. Continuing workflow...")
                                response = requests.post(f"{BASE_URL}/chat", json={
                                    "customer_id": "CUST001",
                                    "application_id": app_id,
                                    "message": "Continue"
                                })
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    print(f"✅ Agent: {data['agent_name']}")
                                    print(f"📝 Message: {data['message']}\n")
                                    
                                    # Check if salary is needed
                                    if "salary" in data['message'].lower():
                                        print("9. Providing salary...")
                                        response = requests.post(f"{BASE_URL}/chat", json={
                                            "customer_id": "CUST001",
                                            "application_id": app_id,
                                            "message": "My salary is 80000"
                                        })
                                        
                                        if response.status_code == 200:
                                            data = response.json()
                                            print(f"✅ Agent: {data['agent_name']}")
                                            print(f"📝 Message: {data['message']}\n")
                                    
                                    # Get final application status
                                    print("10. Getting application status...")
                                    response = requests.get(f"{BASE_URL}/application/{app_id}")
                                    if response.status_code == 200:
                                        app_data = response.json()
                                        print(f"📊 Final Status: {app_data['status']}")
                                        
                                        if app_data.get('sanction_letter_path'):
                                            print(f"📄 Sanction Letter: Available for download")
                                            print(f"🔗 Download URL: {BASE_URL}/sanction-letter/{app_id}")
        
        print("\n🎉 Workflow test completed!")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_loan_workflow()