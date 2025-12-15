# AI Loan Processing System

A comprehensive AI-driven loan processing system with multiple specialized agents orchestrated through AI Agents and exposed via FastAPI.

## Architecture

### Agents
- **Master Agent**: Initial customer interaction and loan interest generation
- **Sales Agent**: Loan details discussion (amount, rate, tenure)
- **Verification Agent**: KYC validation via mock APIs
- **Underwriting Agent**: Credit score fetching and assessment
- **Eligibility Agent**: Decision making based on credit score and loan amount
- **PDF Agent**: Sanction letter generation

### Workflow
1. **Master Agent**: Customer initiates chat → collects name & email → generates loan interest
2. **Sales Agent**: Discusses loan amount & tenure → calculates EMI with interest rate slabs
3. **Verification Agent**: Validates PAN/Aadhar through mock KYC APIs
4. **Underwriting Agent**: Fetches credit score → sets pre-approved limits based on score
5. **Eligibility Agent**: Makes approval/rejection decisions → checks EMI-to-salary ratio
6. **PDF Agent**: Generates sanction letter → uploads to cloud → sends email notification

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
```bash
cp .env.sample .env
# Add your GROQ_API_KEY and other credentials
```

### 3. Run the Server
```bash
uvicorn app:app --reload
```
Server: `http://localhost:8000`

**Production**: `https://ai-loan-advisor-zeta.vercel.app/`

### 4. Test the API
```bash
uv run python test_client.py
```

## API Endpoints

### POST /chat
Start or continue loan conversation
```json
{
  "customer_id": "CUST001",
  "message": "Hello",
  "application_id": "optional-for-continuing",
  "data_update": {"optional": "data"}
}
```

### GET /application/{app_id}
Get application details

### GET /sanction-letter/{app_id}
Download PDF sanction letter

### GET /health
Health check endpoint

## Example Usage

```python
import requests

# Start conversation
response = requests.post("http://localhost:8000/chat", json={
    "customer_id": "CUST001",
    "message": "Hello, I need a loan"
})

app_id = response.json()["application_id"]

# Continue conversation
response = requests.post("http://localhost:8000/chat", json={
    "customer_id": "CUST001",
    "application_id": app_id,
    "message": "My name is John Doe"
})
```

## Decision Logic

### Instant Approval
- Loan amount ≤ Pre-approved limit
- Credit score ≥ 700

### Conditional Approval
- Requires salary verification
- EMI ≤ 50% of salary

### Rejection Criteria
- KYC verification failure
- EMI > 50% of salary
- Credit score too low

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Comprehensive system architecture
- **[Testing Guide](TESTING_GUIDE.md)** - Complete testing procedures
- **[How It Works](HOW_IT_WORKS.md)** - Detailed workflow explanation
- **[Agent Workflow](docs/agent_workflow.md)** - Visual diagrams and flow charts

## File Structure
```
├── loan_advisor/
│   ├── agents/          # Agent implementations
│   ├── models/          # Data models
│   └── services/        # Orchestrator and integrations
├── docs/            # Architecture and workflow diagrams
├── tests/           # Test scripts and scenarios
├── app.py           # FastAPI application
└── sanction_letters/ # Generated PDFs
```