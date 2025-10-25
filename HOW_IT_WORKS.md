# How the AI Loan Processing System Works

## 🏗️ Architecture Overview

### 1. **Multi-Agent System**
The system uses specialized agents, each handling specific parts of the loan workflow:

```
Customer Message → Orchestrator → Current Agent → LLM → Response → Next Agent
```

### 2. **Key Components**

#### **LLM Integration (Groq)**
- **File**: `services/llm_service.py`
- **Purpose**: Generates natural, contextual responses for each agent
- **Model**: Llama3-8B-8192 via Groq API
- **Fallback**: Hardcoded responses if API fails

#### **Agent System**
- **Base Agent**: `agents/base_agent.py` - Common functionality
- **Specialized Agents**: Each handles specific workflow stage
- **Context Aware**: Agents receive application state and generate appropriate responses

#### **Orchestrator**
- **File**: `services/loan_orchestrator.py`
- **Purpose**: Routes messages between agents, manages application state
- **Smart Parsing**: Extracts data from user messages (amounts, names, documents)

#### **FastAPI Server**
- **File**: `main.py`
- **Purpose**: HTTP endpoints for external integration
- **Stateful**: Maintains conversation context across requests

## 🔄 Workflow Explanation

### **Step 1: Customer Initiation**
```python
POST /chat
{
  "customer_id": "CUST001",
  "message": "Hello"
}
```

**What happens:**
1. Orchestrator creates new `LoanApplication`
2. Routes to `MasterAgent`
3. LLM generates welcoming response asking for name
4. Returns response with `action_required: "collect_name"`

### **Step 2: Data Collection**
```python
POST /chat
{
  "customer_id": "CUST001", 
  "application_id": "app_123",
  "message": "My name is John Doe"
}
```

**What happens:**
1. Orchestrator extracts name from message using regex
2. Updates `application.customer.name = "John Doe"`
3. MasterAgent generates interest in loans
4. Sets `next_agent: "sales_agent"`

### **Step 3: Agent Transitions**
Each agent determines the next step based on:
- **Current application state**
- **Required data completeness**
- **Business logic rules**

```python
# Example from SalesAgent
if not application.loan_amount:
    return "Ask for loan amount"
elif not application.tenure_months:
    return "Ask for tenure"
else:
    return "Present summary, move to verification"
```

### **Step 4: LLM Response Generation**
```python
# In each agent
context = {
    "customer_name": "John Doe",
    "status": "sales_discussion", 
    "loan_amount": 500000
}

llm_response = await self.llm.generate_response(
    agent_name="Sales Agent",
    context=context,
    user_message="I need 5 lakh"
)
```

**LLM receives:**
- **System prompt** specific to agent role
- **Current context** (customer data, loan status)
- **User message** for natural conversation

## 🧠 Smart Data Extraction

The orchestrator automatically extracts data from natural language:

```python
# From user message: "I need 5 lakh for 2 years"
message = "I need 5 lakh for 2 years"

# Extracts:
loan_amount = 500000  # "5 lakh" → 500000
tenure_months = 24    # "2 years" → 24 months
```

**Extraction patterns:**
- **Names**: "My name is X", "I am X"
- **Amounts**: "5 lakh", "10 crore", "500000"
- **Tenure**: "24 months", "2 years"
- **PAN**: "ABCDE1234F" format
- **Aadhar**: 12-digit numbers

## 🎯 Decision Engine

### **Credit Score Based Logic**
```python
# Underwriting Agent
if credit_score >= 750:
    pre_approved_limit = 1000000
elif credit_score >= 700:
    pre_approved_limit = 500000
else:
    pre_approved_limit = 300000
```

### **Approval Logic**
```python
# Eligibility Agent
if (loan_amount <= pre_approved_limit and credit_score >= 700):
    return "INSTANT APPROVAL"
elif (emi <= 0.5 * salary):
    return "CONDITIONAL APPROVAL"  
else:
    return "REJECTION"
```

## 🔧 Configuration & Setup

### **1. Environment Setup**
```bash
# Install dependencies
uv sync

# Set Groq API key
echo "GROQ_API_KEY=your_key_here" > .env
```

### **2. Agent Customization**
Each agent has specific prompts in `llm_service.py`:

```python
"Sales Agent": f"""You are a Sales Agent specializing in loan products. Your job is to:
1. Discuss loan amounts (ask if not provided)
2. Explain tenure options (12-60 months)  
3. Calculate and present EMI details
4. Set interest rates: ≤5L=10.5%, ≤10L=11.5%, >10L=12.5%

Current context: {base_context}

Be professional, clear about terms, and guide towards KYC verification once details are complete."""
```

### **3. Business Rules**
Modify decision logic in respective agents:
- **Interest rates**: `sales_agent.py`
- **Credit limits**: `underwriting_agent.py`  
- **Approval criteria**: `eligibility_agent.py`

## 🚀 Running the System

### **Development**
```bash
# Start server
uv run python main.py

# Test complete workflow
uv run python test_client.py

# Test LLM integration
uv run python test_llm_integration.py
```

### **Production Considerations**
1. **Database**: Replace in-memory storage with persistent DB
2. **Authentication**: Add JWT/OAuth for customer sessions
3. **Rate Limiting**: Implement API rate limits
4. **Monitoring**: Add logging and metrics
5. **Caching**: Cache LLM responses for common queries

## 🔍 Debugging

### **Check Agent Flow**
```python
# View current application state
GET /application/{app_id}

# Response shows:
{
  "status": "sales_discussion",
  "customer": {"name": "John Doe"},
  "loan_amount": 500000,
  "next_steps": "collect_tenure"
}
```

### **LLM Fallbacks**
If Groq API fails, system uses hardcoded responses ensuring continuity.

### **Message Parsing**
Check `loan_orchestrator.py` `_extract_data_from_message()` for parsing logic.

This architecture provides a scalable, maintainable system where each component has a single responsibility, making it easy to modify business logic, add new agents, or integrate with external systems.