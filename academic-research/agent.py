"""IntelliSurf Research Agent: Comprehensive knowledge analysis, research synthesis, document generation, and multi-domain intelligence."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.academic_newresearch import academic_newresearch_agent
from .sub_agents.academic_websearch import academic_websearch_agent

MODEL = "gemini-2.5-flash"


# academic_coordinator = LlmAgent(
#     name="intellisurf_research_agent",
#     model=MODEL,
#     description=(
#         "IntelliSurf Research Agent specializing in comprehensive knowledge analysis, "
#         "research synthesis across multiple domains, document generation, "
#         "competitive intelligence, strategic analysis, and multi-domain expertise "
#         "spanning technology, business, science, healthcare, and finance"
#     ),
#     instruction=prompt.ACADEMIC_COORDINATOR_PROMPT,
#     output_key="research_analysis",
#     tools=[
#         AgentTool(agent=academic_websearch_agent),
#         AgentTool(agent=academic_newresearch_agent),
#     ],
# )

# root_agent = academic_coordinator
academic_coordinator = LlmAgent(
    name="academic_coordinator",
    model=MODEL,
    description=(
        "analyzing seminal papers provided by the users, "
        "providing research advice, locating current papers "
        "relevant to the seminal paper, generating suggestions "
        "for new research directions, and accessing web resources "
        "to acquire knowledge"
    ),
    instruction=prompt.ACADEMIC_COORDINATOR_PROMPT,
    output_key="seminal_paper",
    tools=[
        AgentTool(agent=academic_websearch_agent),
        AgentTool(agent=academic_newresearch_agent),
    ],
)

root_agent = academic_coordinator