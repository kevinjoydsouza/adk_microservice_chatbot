"""RFP Coordinator Agent for gathering project details from users."""

from google.adk.agents import LlmAgent
# Functions will be automatically wrapped as FunctionTools
import json
import os
from datetime import datetime

MODEL = "gemini-2.0-flash"

def collect_project_details(project_name: str, opportunity_id: str, client_info: str, 
                          deadline: str, requirements: str, file_formats: str) -> dict:
    """Collect and validate project details from user input."""
    details = {
        "project_name": project_name,
        "opportunity_id": opportunity_id,
        "client_info": client_info,
        "deadline": deadline,
        "requirements": requirements,
        "file_formats": file_formats,
        "collected_at": datetime.now().isoformat(),
        "status": "details_collected"
    }
    return details

def validate_project_details(details: dict) -> dict:
    """Validate completeness of project details."""
    required_fields = ["project_name", "opportunity_id", "client_info", "deadline", "requirements"]
    missing_fields = [field for field in required_fields if not details.get(field)]
    
    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "validation_status": "complete" if len(missing_fields) == 0 else "incomplete"
    }

rfp_coordinator_agent = LlmAgent(
    name="rfp_coordinator",
    model=MODEL,
    description=(
        "RFP Coordinator responsible for gathering comprehensive project details "
        "from users including project name, opportunity ID, client information, "
        "deadlines, requirements, and file format preferences."
    ),
    instruction="""
You are the RFP Coordinator Agent. Your primary role is to gather comprehensive project details from users in a conversational and professional manner.

WORKFLOW:
1. Greet the user and explain you'll help collect RFP project details
2. Ask for the following information systematically:
   - Project Name: What is the name/title of this RFP project?
   - Opportunity ID: What is the unique opportunity identifier?
   - Client Information: Who is the client/organization issuing this RFP?
   - Deadline: When is the proposal submission deadline?
   - Requirements: What are the key requirements and scope of work?
   - File Formats: What file formats do you prefer for document uploads?

3. Use the collect_project_details function to store the information
4. Use validate_project_details to ensure all required information is collected
5. If information is missing, politely ask for the missing details
6. Once complete, confirm all details with the user and indicate readiness to proceed

Be conversational, professional, and thorough. Ask one or two questions at a time to avoid overwhelming the user.
""",
    output_key="project_details",
    tools=[
        collect_project_details,
        validate_project_details,
    ],
)
