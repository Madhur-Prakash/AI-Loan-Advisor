# 🧪 Testing Guide - AI Loan Processing System

## Quick Start Testing

### 1. Start the Server
```bash
uv run python main.py
```
Server starts at: `http://localhost:8000`

### 2. Test Methods

#### **Method A: Automated Test Script**
```bash
uv run python test_client.py
```

#### **Method B: Manual API Testing**
Use Postman, curl, or any HTTP client

#### **Method C: Interactive Testing**
```bash
uv run python interactive_test.py
```

## 📋 Complete Test Scenarios

### **Scenario 1: Successful Loan Approval (High Credit Score)**

#### Step 1: Start Conversation
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "message": "Hello"
}
```

**Expected Response:**
```json
{
  "application_id": "uuid-generated",
  "agent_name": "Master Agent",
  "message": "Hello! Welcome to our loan services. I'm here to help you with personal loans. May I know your name?",
  "status": "initiated",
  "action_required": "collect_name"
}
```

#### Step 2: Provide Name
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "uuid-from-step1",
  "message": "My name is John Doe"
}
```

**Expected Response:**
```json
{
  "application_id": "same-uuid",
  "agent_name": "Master Agent", 
  "message": "Hi John Doe! Great to meet you. Have you considered a personal loan? We offer competitive rates starting from 10.5% with flexible tenure options. Would you like to explore this?",
  "status": "sales_discussion",
  "action_required": null
}
```

#### Step 3: Express Interest
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "Yes, I'm interested in a personal loan"
}
```

**Expected Response:**
```json
{
  "agent_name": "Sales Agent",
  "message": "Excellent! Let's discuss your loan requirements. What loan amount are you looking for?",
  "status": "sales_discussion",
  "action_required": "collect_loan_amount"
}
```

#### Step 4: Provide Loan Amount
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid", 
  "message": "I need 3 lakh rupees"
}
```

**Expected Response:**
```json
{
  "agent_name": "Sales Agent",
  "message": "Perfect! For ₹3,00,000, what repayment tenure would you prefer? We offer flexible options from 12 to 60 months.",
  "status": "sales_discussion",
  "action_required": "collect_tenure"
}
```

#### Step 5: Provide Tenure
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "24 months"
}
```

**Expected Response:**
```json
{
  "agent_name": "Sales Agent",
  "message": "Excellent! Here's your loan summary:\nAmount: ₹3,00,000\nInterest Rate: 10.5% p.a.\nTenure: 24 months\nEMI: ₹13,493\n\nTo proceed, I'll need to verify your identity. Shall we continue?",
  "status": "kyc_verification"
}
```

#### Step 6: Provide PAN
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "My PAN is ABCDE1234F"
}
```

**Expected Response:**
```json
{
  "agent_name": "Verification Agent",
  "message": "Thank you for providing your PAN. Now I need your Aadhar number for complete verification.",
  "status": "kyc_verification",
  "action_required": "collect_aadhar"
}
```

#### Step 7: Provide Aadhar
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "123456789012"
}
```

**Expected Response:**
```json
{
  "agent_name": "Verification Agent",
  "message": "KYC verification successful! Your identity has been verified. Now let's check your credit profile.",
  "status": "underwriting"
}
```

#### Step 8: Credit Assessment (Automatic)
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "Continue"
}
```

**Expected Response:**
```json
{
  "agent_name": "Underwriting Agent",
  "message": "Credit assessment completed!\nCredit Score: 750\nPre-approved Limit: ₹10,00,000\n\nProceeding to eligibility check...",
  "status": "eligibility_check"
}
```

#### Step 9: Final Decision (Automatic)
**Request:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "Continue"
}
```

**Expected Response:**
```json
{
  "agent_name": "Eligibility Agent",
  "message": "🎉 Congratulations! Your loan of ₹3,00,000 is INSTANTLY APPROVED!\nProcessing your sanction letter...",
  "status": "approved"
}
```

#### Step 10: PDF Generation (Automatic)
**Expected Final Response:**
```json
{
  "agent_name": "PDF Agent",
  "message": "🎉 Your loan has been approved! Your sanction letter has been generated.\nDocument: sanction_letters/sanction_letter_uuid.pdf\n\nThank you for choosing our services!",
  "status": "completed"
}
```

### **Scenario 2: Conditional Approval (Salary Required)**

Use same steps 1-8, but in step 9:

**Expected Response:**
```json
{
  "agent_name": "Eligibility Agent", 
  "message": "To proceed with your application, please provide your monthly salary:",
  "status": "eligibility_check",
  "action_required": "collect_salary"
}
```

**Provide Salary:**
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "same-uuid",
  "message": "My salary is 50000"
}
```

**Expected Response (Approval):**
```json
{
  "agent_name": "Eligibility Agent",
  "message": "Great! Your EMI-to-salary ratio is 27.0% (within acceptable limits).\nYour loan of ₹3,00,000 is APPROVED!\nGenerating your sanction letter...",
  "status": "approved"
}
```

### **Scenario 3: Rejection (High EMI Ratio)**

Same as Scenario 2, but provide low salary:

**Provide Low Salary:**
```json
{
  "customer_id": "CUST001",
  "application_id": "same-uuid", 
  "message": "My salary is 20000"
}
```

**Expected Response (Rejection):**
```json
{
  "agent_name": "Eligibility Agent",
  "message": "Unfortunately, your EMI-to-salary ratio is 67.5% which exceeds our maximum limit of 50%. Your loan application has been rejected.",
  "status": "rejected"
}
```

## 🔍 Additional API Endpoints

### Get Application Status
```bash
GET http://localhost:8000/application/{application_id}
```

### Download Sanction Letter
```bash
GET http://localhost:8000/sanction-letter/{application_id}
```

### Health Check
```bash
GET http://localhost:8000/health
```

## 🧪 Test Data Variations

### **Different Loan Amounts**
- `"I need 50000"` → 10.5% interest
- `"I need 8 lakh"` → 11.5% interest  
- `"I need 15 lakh"` → 12.5% interest

### **Different Tenure Formats**
- `"24 months"`
- `"2 years"`
- `"36 months"`

### **Natural Language Variations**
- `"My name is John Doe"`
- `"I am Sarah Smith"`
- `"Call me Mike"`

### **Document Formats**
- PAN: `"ABCDE1234F"`
- Aadhar: `"123456789012"`

## 🚨 Error Scenarios

### Invalid Application ID
```json
POST http://localhost:8000/chat
{
  "customer_id": "CUST001",
  "application_id": "invalid-id",
  "message": "Hello"
}
```
**Expected:** `404 - Application not found`

### Missing Required Fields
```json
POST http://localhost:8000/chat
{
  "message": "Hello"
}
```
**Expected:** `422 - Validation Error`

## 📊 Success Metrics

### **Complete Workflow Test**
- ✅ All 10 steps complete without errors
- ✅ PDF file generated in `sanction_letters/`
- ✅ Application status = "completed"
- ✅ Natural language responses from LLM

### **Performance Test**
- ✅ Each API call responds within 2 seconds
- ✅ LLM responses are contextually appropriate
- ✅ Data extraction works for various input formats

Run the automated test script to verify all scenarios:
```bash
uv run python test_client.py
```

## Diagrams

Use the sequence diagram to align test flows with the agent conversation. This helps verify that each test exercises the expected transitions and actions.

- Full workflow docs: `docs/agent_workflow.md`
- Sequence diagram image: `docs/images/sequence-conversation-via-chat.svg`
- Inline preview:

  ![Sequence](docs/images/sequence-conversation-via-chat.svg)

Mapping common tests to the sequence:

- `tests/test_client.py`
  - Runs the end-to-end `/chat` flow: INITIATED → SALES_DISCUSSION → KYC_VERIFICATION → UNDERWRITING → ELIGIBILITY_CHECK → APPROVED → COMPLETED.
  - Verifies messages and `application_id`, then checks `/application/{app_id}` snapshot.

- `tests/test_scenarios.py`
  - Happy path mirrors the full sequence culminating in PDF generation.
  - Denial paths:
    - KYC failure aligns with the VerificationAgent segment (PAN/Aadhar validation → `REJECTED`).
    - Eligibility failure aligns with the EligibilityAgent segment (EMI/salary ratio or pre-approved limit → `REJECTED`).

- `tests/test_kyc_validation.py`
  - Focuses on the KYC step in `KYC_VERIFICATION`: PAN and Aadhar format validation, mock KYC outcome.

- `tests/interactive_test.py`
  - Manual reproduction of the sequence: provide name → loan amount → tenure → PAN → Aadhar → Continue → salary; then verify approval and PDF path.

Tips to exercise specific branches (tie-ins to diagram steps):

- Set `KYC_SUCCESS_RATE` env var to influence the VerificationAgent step (e.g., `KYC_SUCCESS_RATE=0.20` for more failures).
- Adjust `salary` to move the EligibilityAgent decision over/under the EMI threshold.
- After approval, use `GET /sanction-letter/{app_id}` to validate the final PDF step.