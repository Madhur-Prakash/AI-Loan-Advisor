import json
from fastapi.exceptions import HTTPException
from fastapi import status
import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Set default Groq API key and model from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")

# Check if Groq API key is available
if not GROQ_API_KEY:
    print("WARNING: No Groq API key found in environment variables. API will not function properly.")

def generate_email(recipient_email: str, context: str):
    try:
        # Initialize LLM with the API key
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=DEFAULT_MODEL
        )
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
    ("system",
     """
You are an AI email assistant for SYNFIN, an AI-driven loan processing system. Your task is to draft professional emails based on loan application context.

Context: {context}

Email Guidelines:
- Use SYNFIN as the company name
- Maintain professional, empathetic tone
- Include relevant loan details (amount, EMI, tenure, interest rate, credit score, pre-approved limit)
- For approvals: congratulate and provide next steps
- For rejections: be empathetic and suggest actionable alternatives
- For pending actions: clearly state required documents or information
- At the last of the email, include a disclaimer: "This is an automated email from SYNFIN. Please do not reply to this email."

Generate ONLY a valid JSON response with this exact structure (no preamble, no explanation):
{{
    "recipient_email": "{recipient_email}",
    "subject": "[Concise subject line based on loan status]",
    "body": "[Professional HTML-formatted email body]"
}}

IMPORTANT: Return ONLY the JSON object, nothing else.
"""),
     
    ("user", 
     "Draft a professional email for the loan application based on the context. Include customer name, loan status, and relevant financial details. Format the body as HTML for better readability."),

    ("assistant", 
     "I will generate a professional email in JSON format with appropriate subject and HTML body based on the loan application context.")
    ])

        
        # Create and invoke the chain
        chain = prompt | llm | StrOutputParser()
        generated_email = chain.invoke({"context": context, "recipient_email": recipient_email})
        # print("✉️Generated Email:", generated_email)
        return generated_email
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating email: {str(e)}")
    

def convert_string_to_json(json_string: str):
    try:
        print("received json_string:", json_string)
        
        # Remove markdown code blocks
        if json_string.startswith("```"):
            json_string = json_string.strip("`")
            json_string = json_string.replace("json", "", 1).strip()
        
        # Remove any preamble text before the JSON (e.g., "Here is the response:")
        if "{" in json_string:
            json_string = json_string[json_string.index("{"):]
        
        # Find the last closing brace to handle any trailing text
        if "}" in json_string:
            json_string = json_string[:json_string.rindex("}")+1]
        
        json_object = json.loads(json_string)
        print("="*60)
        print("Converted JSON object:", json_object)
        return json_object
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON string: {e}")
        print(f"Attempted to parse: {json_string[:200]}...")
        return None