import requests

BASE_URL = "http://localhost:8000"

def interactive_test():
    print("🚀 Interactive AI Loan Processing Test")
    print("=" * 50)
    
    customer_id = input("Enter Customer ID (or press Enter for CUST001): ").strip() or "CUST001"
    app_id = None
    
    print(f"\nStarting conversation for customer: {customer_id}")
    print("Type 'quit' to exit, 'status' to check application status")
    print("-" * 50)
    
    while True:
        message = input("\nYou: ").strip()
        
        if message.lower() == 'quit':
            break
            
        if message.lower() == 'status' and app_id:
            response = requests.get(f"{BASE_URL}/application/{app_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"\n📊 Application Status:")
                print(f"Status: {data['status']}")
                print(f"Customer: {data['customer']['name'] or 'Not provided'}")
                print(f"Loan Amount: {data['loan_amount'] or 'Not specified'}")
                print(f"Credit Score: {data['customer']['credit_score'] or 'Not assessed'}")
            continue
            
        if not message:
            continue
            
        # Prepare request
        payload = {
            "customer_id": customer_id,
            "message": message
        }
        
        if app_id:
            payload["application_id"] = app_id
            
        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                app_id = data["application_id"]
                
                print(f"\n🤖 {data['agent_name']}: {data['message']}")
                print(f"📍 Status: {data['status']}")
                
                if data.get('action_required'):
                    print(f"⚡ Action Required: {data['action_required']}")
                    
                # Check if completed and offer PDF download
                if data['status'] == 'completed':
                    print(f"\n📄 Sanction letter available at:")
                    print(f"   {BASE_URL}/sanction-letter/{app_id}")
                    
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Error: Cannot connect to server. Make sure it's running on localhost:8000")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    interactive_test()