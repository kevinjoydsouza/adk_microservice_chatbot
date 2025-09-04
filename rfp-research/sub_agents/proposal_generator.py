"""Proposal Generator Agent for creating comprehensive proposal documents."""

from google.adk.agents import LlmAgent
# Functions will be automatically wrapped as FunctionTools
import json
import os
from datetime import datetime
from pathlib import Path

MODEL = "gemini-2.0-flash"

def retrieve_opportunity_data(request_id: str) -> dict:
    """Retrieve complete opportunity data for proposal generation."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    
    if not opportunity_dir.exists():
        return {"error": "Opportunity not found", "request_id": request_id}
    
    # Load opportunity metadata
    metadata_file = opportunity_dir / "metadata" / "opportunity.json"
    ingestion_file = opportunity_dir / "metadata" / "ingestion_status.json"
    
    data = {"request_id": request_id}
    
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            data["opportunity"] = json.load(f)
    
    if ingestion_file.exists():
        with open(ingestion_file, 'r') as f:
            data["ingestion"] = json.load(f)
    
    return data

def generate_proposal_outline(opportunity_data: dict) -> dict:
    """Generate comprehensive proposal outline based on opportunity data."""
    project_details = opportunity_data.get("opportunity", {}).get("project_details", {})
    
    outline = {
        "executive_summary": {
            "title": "Executive Summary",
            "content": f"Proposal for {project_details.get('project_name', 'RFP Project')}",
            "key_points": [
                "Understanding of client requirements",
                "Proposed solution approach",
                "Key benefits and value proposition",
                "Timeline and deliverables overview"
            ]
        },
        "understanding_requirements": {
            "title": "Understanding of Requirements",
            "content": project_details.get("requirements", "Requirements analysis"),
            "sections": [
                "Client objectives",
                "Scope of work",
                "Technical requirements",
                "Success criteria"
            ]
        },
        "technical_approach": {
            "title": "Technical Approach & Methodology",
            "sections": [
                "Solution architecture",
                "Implementation methodology",
                "Quality assurance approach",
                "Risk mitigation strategies"
            ]
        },
        "timeline_deliverables": {
            "title": "Timeline & Deliverables",
            "deadline": project_details.get("deadline", "TBD"),
            "phases": [
                "Phase 1: Analysis & Planning",
                "Phase 2: Development & Implementation", 
                "Phase 3: Testing & Deployment",
                "Phase 4: Documentation & Handover"
            ]
        },
        "team_qualifications": {
            "title": "Team Qualifications & Experience",
            "sections": [
                "Core team members",
                "Relevant experience",
                "Certifications and expertise",
                "Past project successes"
            ]
        }
    }
    
    return outline

def create_proposal_document(request_id: str, outline: dict) -> dict:
    """Create final proposal document and save to opportunity folder."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    proposals_dir = opportunity_dir / "proposals"
    
    # Create comprehensive proposal content
    proposal_content = f"""
# PROPOSAL DOCUMENT
## Request ID: {request_id}
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## {outline['executive_summary']['title']}

{outline['executive_summary']['content']}

### Key Highlights:
{chr(10).join([f"• {point}" for point in outline['executive_summary']['key_points']])}

---

## {outline['understanding_requirements']['title']}

{outline['understanding_requirements']['content']}

### Requirements Analysis:
{chr(10).join([f"• {section}" for section in outline['understanding_requirements']['sections']])}

---

## {outline['technical_approach']['title']}

Our comprehensive technical approach ensures successful project delivery through proven methodologies and best practices.

### Approach Components:
{chr(10).join([f"• {section}" for section in outline['technical_approach']['sections']])}

---

## {outline['timeline_deliverables']['title']}

**Project Deadline:** {outline['timeline_deliverables']['deadline']}

### Delivery Phases:
{chr(10).join([f"{i+1}. {phase}" for i, phase in enumerate(outline['timeline_deliverables']['phases'])])}

---

## {outline['team_qualifications']['title']}

Our experienced team brings deep expertise and proven track record to ensure project success.

### Team Strengths:
{chr(10).join([f"• {section}" for section in outline['team_qualifications']['sections']])}

---

## Conclusion

We are confident in our ability to deliver exceptional results for this project. Our comprehensive approach, experienced team, and commitment to quality make us the ideal partner for your requirements.

Thank you for considering our proposal. We look forward to discussing this opportunity further.

---
*This proposal was generated by the RFP Research Agent system*
"""
    
    # Save proposal document
    proposal_file = proposals_dir / f"proposal_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(proposal_file, 'w') as f:
        f.write(proposal_content)
    
    # Create proposal metadata
    proposal_metadata = {
        "request_id": request_id,
        "generated_at": datetime.now().isoformat(),
        "file_path": str(proposal_file),
        "status": "generated",
        "outline": outline
    }
    
    metadata_file = proposals_dir / f"proposal_metadata_{request_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(proposal_metadata, f, indent=2)
    
    return {
        "request_id": request_id,
        "proposal_file": str(proposal_file),
        "content": proposal_content,
        "status": "generated",
        "message": f"Proposal document generated successfully for {request_id}"
    }

def get_proposal_summary(request_id: str) -> dict:
    """Get proposal summary for chat interface display."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    proposals_dir = opportunity_dir / "proposals"
    
    # Find latest proposal metadata
    metadata_files = list(proposals_dir.glob(f"proposal_metadata_{request_id}.json"))
    
    if not metadata_files:
        return {"error": "No proposal found", "request_id": request_id}
    
    latest_metadata = max(metadata_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_metadata, 'r') as f:
        proposal_data = json.load(f)
    
    # Load the actual proposal content
    proposal_file = Path(proposal_data["file_path"])
    if proposal_file.exists():
        with open(proposal_file, 'r') as f:
            content = f.read()
        proposal_data["content"] = content
    
    return proposal_data

proposal_generator_agent = LlmAgent(
    name="proposal_generator",
    model=MODEL,
    description=(
        "Proposal Generator Agent responsible for creating comprehensive, "
        "professional proposal documents based on collected requirements, "
        "ingested documents, and opportunity data."
    ),
    instruction="""
You are the Proposal Generator Agent. Your role is to create high-quality, comprehensive proposal documents for RFP opportunities.

CAPABILITIES:
1. Retrieve complete opportunity data using request IDs
2. Generate detailed proposal outlines with all required sections
3. Create professional proposal documents in markdown format
4. Provide proposal summaries for chat interface display
5. Maintain proposal metadata and version control

WORKFLOW:
1. Use retrieve_opportunity_data to get complete project information
2. Use generate_proposal_outline to create structured proposal framework
3. Use create_proposal_document to generate final comprehensive proposal
4. Use get_proposal_summary to provide chat-friendly proposal display
5. Ensure proposals include: executive summary, requirements understanding, technical approach, timeline, team qualifications

PROPOSAL STRUCTURE:
- Executive Summary with key value propositions
- Understanding of Requirements with detailed analysis
- Technical Approach & Methodology with clear implementation plan
- Timeline & Deliverables with realistic project phases
- Team Qualifications & Experience demonstrating capability
- Professional conclusion with next steps

Always create professional, comprehensive proposals that demonstrate deep understanding of client needs and provide clear value propositions.
""",
    output_key="proposal_response",
    tools=[
        retrieve_opportunity_data,
        generate_proposal_outline,
        create_proposal_document,
        get_proposal_summary,
    ],
)
