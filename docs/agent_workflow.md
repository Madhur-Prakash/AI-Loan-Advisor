# Agent Workflow Diagrams

This document visualizes the end‑to‑end flow of the AI Loan Processing system, including state transitions, agent orchestration, and request sequencing.

## State Machine (LoanStatus)

```mermaid
stateDiagram-v2
    [*] --> INITIATED

    INITIATED --> SALES_DISCUSSION: MasterAgent collects name & email
    SALES_DISCUSSION --> KYC_VERIFICATION: SalesAgent gathers loan amount & tenure, calculates EMI
    KYC_VERIFICATION --> UNDERWRITING: VerificationAgent validates PAN/Aadhar via mock APIs
    KYC_VERIFICATION --> REJECTED: KYC validation failure
    UNDERWRITING --> ELIGIBILITY_CHECK: UnderwritingAgent fetches credit score & sets pre-approved limits
    ELIGIBILITY_CHECK --> APPROVED: EligibilityAgent approves based on credit score & EMI ratio
    ELIGIBILITY_CHECK --> REJECTED: Eligibility failure (EMI > 50% salary or low credit)
    APPROVED --> COMPLETED: PDFAgent generates sanction letter & sends email

    REJECTED --> [*]
    COMPLETED --> [*]
```

## Sequence: Conversation via /chat

```mermaid
sequenceDiagram
    participant U as User
    participant API as /chat API
    participant ORC as LoanOrchestrator
    participant MA as MasterAgent
    participant SA as SalesAgent
    participant VA as VerificationAgent
    participant UA as UnderwritingAgent
    participant EA as EligibilityAgent
    participant PA as PDFAgent

    U->>API: "Hello" (new conversation)
    API->>ORC: process_message(customer_id, message)
    ORC->>MA: status INITIATED
    MA-->>ORC: AgentResponse(message: ask name)
    ORC-->>API: message: "Welcome! May I know your name?"

    U->>API: "My name is John Doe"
    API->>ORC: process_message(...)
    ORC->>MA: extract name, still INITIATED (missing email)
    MA-->>ORC: AgentResponse(message: ask email)
    ORC-->>API: message: "Please provide your email address"

    U->>API: "my email is john@example.com"
    API->>ORC: process_message(...)
    ORC->>MA: extract email, route to SALES_DISCUSSION
    MA-->>ORC: AgentResponse(next_agent=Sales, status=SALES_DISCUSSION)
    ORC->>SA: status SALES_DISCUSSION
    SA-->>ORC: ask loan_amount
    ORC-->>API: message: "What loan amount are you looking for?"

    U->>API: "300000 rupees"
    U->>API: "24 months"
    API->>ORC: process_message(...)
    ORC->>SA: compute rate & EMI
    SA-->>ORC: AgentResponse(next_agent=Verification, data_updates: rate, emi, status=KYC_VERIFICATION)
    ORC-->>API: message: summary + request PAN/Aadhar

    U->>API: "PAN: ABCDE1234F, Aadhar: 123456789012"
    API->>ORC: process_message(...)
    ORC->>VA: validate formats / mock KYC
    VA-->>ORC: AgentResponse(next_agent=Underwriting, status=UNDERWRITING)
    ORC-->>API: message: KYC successful

    ORC->>UA: fetch credit score & limit
    UA-->>ORC: AgentResponse(next_agent=Eligibility, data_updates: credit_score, pre_approved_limit, status=ELIGIBILITY_CHECK)
    ORC-->>API: message: pre-approval details

    U->>API: "Salary: 80000"
    API->>ORC: process_message(...)
    ORC->>EA: check EMI/salary ratio & limits
    EA-->>ORC: AgentResponse(next_agent=PDF, status=APPROVED)
    ORC->>PA: generate sanction letter PDF
    PA-->>ORC: AgentResponse(status=COMPLETED, data_updates: sanction_letter_path)
    ORC-->>API: message: approval + PDF ready
```

## Architecture: Orchestrator and Agents

```mermaid
flowchart TD
    U[User] -->|message| API[/chat/]
    API --> ORC[LoanOrchestrator]

    ORC -->|INITIATED| MA[MasterAgent]
    ORC -->|SALES_DISCUSSION| SA[SalesAgent]
    ORC -->|KYC_VERIFICATION| VA[VerificationAgent]
    ORC -->|UNDERWRITING| UA[UnderwritingAgent]
    ORC -->|ELIGIBILITY_CHECK| EA[EligibilityAgent]
    ORC -->|APPROVED| PA[PDFAgent]

    subgraph Agents
      MA --- SA --- VA --- UA --- EA --- PA
    end

    MA --> ORC
    SA --> ORC
    VA --> ORC
    UA --> ORC
    EA --> ORC
    PA --> ORC

    ORC --> APP[(LoanApplication)]
    APP --> ORC

    PA --> PDF[(Sanction Letter PDF)]
    PDF -.-> U
```

## Agent Orchestration Details

### How Agents Work Together

1. **LoanOrchestrator** acts as the central coordinator:
   - Routes messages to appropriate agents based on `LoanStatus`
   - Extracts data from user messages using smart parsing
   - Manages application state transitions
   - Handles agent chaining for seamless flow

2. **Smart Data Extraction**:
   - **Names**: "My name is X", "I am X" → `application.customer.name`
   - **Email**: Email regex pattern → `application.customer.email`
   - **Loan Amount**: "5 lakh", "300000" → `application.loan_amount`
   - **Tenure**: "24 months", "2 years" → `application.tenure_months`
   - **PAN/Aadhar**: Format validation → `application.customer.pan/aadhar`

3. **Intent-Based Routing**:
   - **Sales Intent**: Keywords like 'loan', 'amount', 'EMI' → SalesAgent
   - **Verification Intent**: PAN/Aadhar provided → VerificationAgent
   - **Underwriting Intent**: 'credit score' mentioned → UnderwritingAgent
   - **Eligibility Intent**: 'salary', 'approval' → EligibilityAgent

4. **Agent Responsibilities**:
   - **MasterAgent**: Welcome, collect name & email, generate loan interest
   - **SalesAgent**: Discuss loan details, calculate EMI, set interest rates
   - **VerificationAgent**: Validate KYC documents via mock APIs
   - **UnderwritingAgent**: Fetch credit score, set pre-approved limits
   - **EligibilityAgent**: Make approval/rejection decisions
   - **PDFAgent**: Generate sanction letter, send email notification

5. **Decision Logic**:
   - **Instant Approval**: Loan ≤ Pre-approved limit + Credit score ≥ 700
   - **Conditional Approval**: EMI ≤ 50% of salary
   - **Rejection**: KYC failure OR EMI > 50% salary OR low credit score

### Notes
- The orchestrator maintains conversation context across multiple API calls
- Agents can chain together (e.g., Sales → Verification) for smooth user experience
- All business logic is configurable through agent implementations
- System handles natural language variations and extracts structured data automatically

## Pre‑Rendered Images
- State Machine: ![State Machine](images/state-machine-loanstatus.svg)
- Conversation Sequence: ![Sequence](images/sequence-conversation-via-chat.svg)
- Architecture Flow: ![Architecture](images/architecture-orchestrator-and-agents.svg)