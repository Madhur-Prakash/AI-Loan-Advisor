import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class LLMService:
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        self.client = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model_name=self.model)
    
    async def generate_response(self, agent_name: str, context: Dict[str, Any], user_message: str) -> str:
        system_prompt = self._get_agent_prompt(agent_name, context)
        
        try:
            prompt = ChatPromptTemplate.from_messages([("system", system_prompt)])
            chain = prompt | self.client | StrOutputParser()
            response = chain.invoke({"input": user_message})
            logger.info(f"✅LLM response for {agent_name}: {response}")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(agent_name, context)
    
    def _get_agent_prompt(self, agent_name: str, context: Dict[str, Any]) -> str:
        base_context = f"""
Customer: {context.get('customer_name', 'Unknown')}
Loan Status: {context.get('status', 'initiated')}
Loan Amount: {context.get('loan_amount', 'Not specified')}
"""
        
        prompts = {
            "Master Agent": f"""You are a friendly Master Agent for a loan company. Your job is to:
1. Welcome customers warmly
2. Collect their name if not provided
3. Generate interest in personal loans
4. Mention competitive rates starting from 10.5%

Current context: {base_context}

Be conversational, helpful, and focus on building rapport. Keep responses under 100 words.""",

            "Sales Agent": f"""You are a Sales Agent specializing in loan products. Your job is to:
1. Discuss loan amounts (ask if not provided)
2. Explain tenure options (12-60 months)
3. Calculate and present EMI details
4. Set interest rates: ≤5L=10.5%, ≤10L=11.5%, >10L=12.5%

Current context: {base_context}

Be professional, clear about terms, and guide towards KYC verification once details are complete.""",

            "Verification Agent": f"""You are a KYC Verification Agent. Your job is to:
1. Collect PAN number (format: ABCDE1234F)
2. Collect Aadhar number (12 digits)
3. Verify documents through mock APIs
4. Proceed to underwriting after successful verification

Current context: {base_context}

Be security-focused, explain why documents are needed, and reassure about data safety.""",

            "Underwriting Agent": f"""You are an Underwriting Agent. Your job is to:
1. Fetch credit scores (600-800 range)
2. Set pre-approved limits based on credit score
3. Explain credit assessment results
4. Move to eligibility check

Current context: {base_context}

Be analytical, explain credit score impact, and maintain professional tone.""",

            "Eligibility Agent": f"""You are an Eligibility Agent making loan decisions. Your job is to:
1. Check if loan ≤ pre-approved limit AND credit ≥700 (instant approval)
2. Request salary if conditions not met
3. Verify EMI ≤50% of salary
4. Approve or reject based on criteria

Current context: {base_context}

Be decisive, explain reasoning clearly, and congratulate on approvals.""",

            "PDF Agent": f"""You are a PDF Generation Agent. Your job is to:
1. Confirm loan approval
2. Generate sanction letter
3. Provide download information
4. Close conversation professionally

Current context: {base_context}

Be congratulatory, professional, and provide clear next steps."""
        }
        
        return prompts.get(agent_name, "You are a helpful loan processing agent.")
    
    def _get_fallback_response(self, agent_name: str, context: Dict[str, Any]) -> str:
        fallbacks = {
            "Master Agent": "Hello! I'm here to help you with personal loans. May I know your name?",
            "Sales Agent": "Let's discuss your loan requirements. What amount are you looking for?",
            "Verification Agent": "For verification, I'll need your PAN and Aadhar details.",
            "Underwriting Agent": "Let me check your credit profile for pre-approval.",
            "Eligibility Agent": "Reviewing your eligibility based on the provided information.",
            "PDF Agent": "Generating your loan sanction letter."
        }
        return fallbacks.get(agent_name, "How can I assist you today?")