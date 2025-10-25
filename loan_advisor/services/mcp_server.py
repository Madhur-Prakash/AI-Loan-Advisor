import asyncio
from typing import Dict, Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from agents.master_agent import MasterAgent
from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.eligibility_agent import EligibilityAgent
from agents.pdf_agent import PDFAgent
from models.loan_models import LoanApplication, Customer, LoanStatus

class LoanMCPServer:
    def __init__(self):
        self.server = Server("loan-processing-server")
        self.agents = {
            "master_agent": MasterAgent(),
            "sales_agent": SalesAgent(),
            "verification_agent": VerificationAgent(),
            "underwriting_agent": UnderwritingAgent(),
            "eligibility_agent": EligibilityAgent(),
            "pdf_agent": PDFAgent()
        }
        self.applications: Dict[str, LoanApplication] = {}
        self._setup_tools()
    
    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="process_loan_application",
                    description="Process loan application through various agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "application_id": {"type": "string"},
                            "customer_id": {"type": "string"},
                            "message": {"type": "string"},
                            "data_update": {"type": "object"}
                        },
                        "required": ["application_id", "customer_id", "message"]
                    }
                ),
                Tool(
                    name="get_application_status",
                    description="Get current status of loan application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "application_id": {"type": "string"}
                        },
                        "required": ["application_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            if name == "process_loan_application":
                return await self._process_application(arguments)
            elif name == "get_application_status":
                return await self._get_status(arguments)
    
    async def _process_application(self, args: Dict[str, Any]):
        app_id = args["application_id"]
        customer_id = args["customer_id"]
        message = args["message"]
        data_update = args.get("data_update", {})
        
        # Get or create application
        if app_id not in self.applications:
            self.applications[app_id] = LoanApplication(
                application_id=app_id,
                customer=Customer(customer_id=customer_id)
            )
        
        application = self.applications[app_id]
        
        # Update application data
        if data_update:
            self._update_application(application, data_update)
        
        # Determine current agent
        current_agent = self._get_current_agent(application)
        
        # Process with agent
        response = await current_agent.process(application, message)
        
        # Update application with response data
        if response.data_updates:
            self._update_application(application, response.data_updates)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "agent_response": response.dict(),
                "application_status": application.dict()
            })
        )]
    
    async def _get_status(self, args: Dict[str, Any]):
        app_id = args["application_id"]
        if app_id in self.applications:
            return [TextContent(
                type="text",
                text=json.dumps(self.applications[app_id].dict())
            )]
        return [TextContent(type="text", text="Application not found")]
    
    def _get_current_agent(self, application: LoanApplication):
        status = application.status
        
        if status == LoanStatus.INITIATED:
            return self.agents["master_agent"]
        elif status == LoanStatus.SALES_DISCUSSION:
            return self.agents["sales_agent"]
        elif status == LoanStatus.KYC_VERIFICATION:
            return self.agents["verification_agent"]
        elif status == LoanStatus.UNDERWRITING:
            return self.agents["underwriting_agent"]
        elif status == LoanStatus.ELIGIBILITY_CHECK:
            return self.agents["eligibility_agent"]
        elif status == LoanStatus.APPROVED:
            return self.agents["pdf_agent"]
        else:
            return self.agents["master_agent"]
    
    def _update_application(self, application: LoanApplication, updates: Dict[str, Any]):
        for key, value in updates.items():
            if hasattr(application, key):
                setattr(application, key, value)
            elif hasattr(application.customer, key):
                setattr(application.customer, key, value)
    
    async def run(self, transport):
        await self.server.run(transport)