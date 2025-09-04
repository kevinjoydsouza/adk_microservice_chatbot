"""RFP Research Agent: Comprehensive RFP processing, opportunity management, and proposal generation."""

from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.rfp_coordinator import rfp_coordinator_agent
from .sub_agents.teamcentre_mock import teamcentre_mock_agent
from .sub_agents.document_ingestion import document_ingestion_agent
from .sub_agents.proposal_generator import proposal_generator_agent

MODEL = "gemini-2.0-flash"

# Main RFP Research Agent with parallel processing capabilities
rfp_research_agent = LlmAgent(
    name="rfp_research_agent",
    model=MODEL,
    description=(
        "RFP Research Agent specializing in comprehensive RFP processing, "
        "opportunity management, document ingestion, and proposal generation. "
        "Handles user queries for project details, creates opportunities in TeamCentre, "
        "manages file uploads, and generates final proposal documents."
    ),
    instruction=prompt.RFP_RESEARCH_PROMPT,
    output_key="rfp_analysis",
    tools=[
        AgentTool(agent=rfp_coordinator_agent),
        AgentTool(agent=teamcentre_mock_agent),
        AgentTool(agent=document_ingestion_agent),
        AgentTool(agent=proposal_generator_agent),
    ],
)

root_agent = rfp_research_agent
