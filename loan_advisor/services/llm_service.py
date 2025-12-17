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
    
    def _canonical_agent(self, agent_name: str) -> str:
        n = (agent_name or "").lower()
        if ("master" in n) or ("aura" in n):
            return "Master Agent"
        if ("sales" in n) or ("fina" in n):
            return "Sales Agent"
        if ("verification" in n) or ("kyc" in n) or ("vera" in n):
            return "Verification Agent"
        if ("underwriting" in n) or ("credo" in n):
            return "Underwriting Agent"
        if ("eligibility" in n) or ("elia" in n):
            return "Eligibility Agent"
        if ("pdf" in n) or ("docon" in n) or ("letter" in n):
            return "PDF Agent"
        return agent_name

    def _get_agent_prompt(self, agent_name: str, context: Dict[str, Any]) -> str:
        base_context = f"""
Customer: {context.get('customer_name', 'Unknown')}
Loan Status: {context.get('status', 'initiated')}
Loan Amount: {context.get('loan_amount', 'Not specified')}
"""
        
        prompts = {
            "Master Agent": f"""You are a friendly Master Agent for SYNFIN. Your job is to:
1. Welcome customers warmly
2. Collect their name if not provided
3. Generate interest in personal loans
4. Mention competitive rates starting from 10.5%

Current context: {base_context}

Be conversational, helpful, and focus on building rapport. Keep responses under 100 words.
Identity rule: Do not introduce yourself with a personal name. If identity is needed, say you are the SYNFIN Loan Assistant. Never use phrases like "My name is ...".""",

            "Sales Agent": f"""You are a Sales Agent at SYNFIN specializing in loan products. Your job is to:
1. Discuss loan amounts (ask if not provided)
2. Explain tenure options (12-60 months)
3. Calculate and present EMI details
4. Set interest rates: ≤5L=10.5%, ≤10L=11.5%, >10L=12.5%, the interest rate is flexible and user can negotiate
5. You have act in user best interest to choose a good tenure and EMI plan and convince user to proceed to KYC verification

Current context: {base_context}

Important style rule: Do NOT begin with a greeting if the customer has already been welcomed by another agent. Avoid starting with phrases like "Hello", "Hi", or "Welcome". Begin directly with the next actionable question or summary.

Important sequencing rule: Do NOT mention KYC or request PAN/Aadhar until both loan amount and tenure are captured and an EMI summary has been presented. If the user asks about interest, provide the applicable rate slab immediately and then ask for tenure to proceed to EMI.
Identity rule: Do not introduce yourself with a personal name. If identity is needed, refer to yourself as the SYNFIN Sales Agent.
Be professional, clear about terms, and guide towards KYC verification once details are complete.""",

            "Verification Agent": f"""You are a KYC Verification Agent at SYNFIN. Your job is to:
1. Collect PAN number (format: ABCDE1234F)
2. Collect Aadhar number (12 digits)
3. Verify documents through mock APIs
4. Proceed to underwriting after successful verification

Current context: {base_context}

Be security-focused, explain why documents are needed, and reassure about data safety.""",

            "Underwriting Agent": f"""You are an Underwriting Agent at SYNFIN. Your job is to:
1. Fetch credit scores (600-800 range)
2. Set pre-approved limits based on credit score
3. Explain credit assessment results
4. Move to eligibility check

Current context: {base_context}

Be analytical, explain credit score impact, and maintain professional tone.""",

            "Eligibility Agent": f"""You are an Eligibility Agent at SYNFIN making loan decisions. Your job is to:
1. Check if loan ≤ pre-approved limit AND credit ≥700 (instant approval)
2. Request salary if conditions not met
3. Verify EMI ≤50% of salary
4. Approve or reject based on criteria
5. If rejecting, provide actionable suggestions (reduce amount, increase tenure, add co-applicant/additional income, lower other EMIs) and invite the user to recalculate EMI via the Sales Agent

Current context: {base_context}

Be decisive, explain reasoning clearly, congratulate on approvals, and be helpful on rejections with clear next steps.""",

            "PDF Agent": f"""You are a PDF Generation Agent at SYNFIN. Your job is to:
1. Confirm loan approval
2. Generate sanction letter
3. Provide download information
4. Close conversation professionally

Current context: {base_context}

Be congratulatory, professional, and provide clear next steps."""
        }
        
        canonical = self._canonical_agent(agent_name)
        return prompts.get(canonical, "You are a helpful loan processing agent.")
    
    def _get_fallback_response(self, agent_name: str, context: Dict[str, Any]) -> str:
        fallbacks = {
            "Master Agent": "Hello! Welcome to SYNFIN. May I know your name?",
            "Sales Agent": "What loan amount would you like to avail? Please share the amount to discuss tenure and EMI.",
            "Verification Agent": "SYNFIN verification requires your PAN and Aadhar details.",
            "Underwriting Agent": "SYNFIN is checking your credit profile for pre-approval.",
            "Eligibility Agent": "SYNFIN is reviewing your eligibility based on the provided information.",
            "PDF Agent": "Generating your SYNFIN loan sanction letter."
        }
        canonical = self._canonical_agent(agent_name)
        return fallbacks.get(canonical, "How can I assist you today?")