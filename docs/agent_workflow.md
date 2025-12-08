# Agent Workflow Diagrams

This document visualizes the end‑to‑end flow of the Loan Advisor system, including state transitions, agent orchestration, and request sequencing.

## State Machine (LoanStatus)

```mermaid
stateDiagram-v2
    [*] --> INITIATED

    INITIATED --> SALES_DISCUSSION: MasterAgent collects name
    SALES_DISCUSSION --> KYC_VERIFICATION: SalesAgent gathers loan & tenure, sets EMI/rate
    KYC_VERIFICATION --> UNDERWRITING: VerificationAgent validates PAN/Aadhar
    KYC_VERIFICATION --> REJECTED: KYC failure
    UNDERWRITING --> ELIGIBILITY_CHECK: UnderwritingAgent sets credit score & pre-approved limit
    ELIGIBILITY_CHECK --> APPROVED: EligibilityAgent EMI/salary within limits
    ELIGIBILITY_CHECK --> REJECTED: Eligibility failure (ratio/limits)
    APPROVED --> COMPLETED: PDFAgent generates sanction letter (PDF)

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
    MA-->>ORC: AgentResponse(next_agent=Sales, data_updates: status=SALES_DISCUSSION)
    ORC-->>API: message: ask name

    U->>API: "My name is ..."
    API->>ORC: process_message(...)
    ORC->>SA: status SALES_DISCUSSION
    SA-->>ORC: ask loan_amount & tenure
    ORC-->>API: message: request loan details

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

## Notes
- The orchestrator selects the agent based on `LoanStatus`, applies `AgentResponse.data_updates`, and may auto-advance to `next_agent` to reduce user steps.
- Failures (KYC or eligibility) set `status=REJECTED` with a `rejection_reason` and end the flow.
- `PDFAgent` finalizes approval by generating a sanction letter and setting `status=COMPLETED`.

## Pre‑Rendered Images
- State Machine: ![State Machine](images/state-machine-loanstatus.svg)
- Conversation Sequence: ![Sequence](images/sequence-conversation-via-chat.svg)
- Architecture Flow: ![Architecture](images/architecture-orchestrator-and-agents.svg)