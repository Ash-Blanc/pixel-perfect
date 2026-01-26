"""Architect agent for designing the Nuxt.js migration plan."""

from agno.agent import Agent

from app.config import get_model
from app.schemas import MigrationPlan


def create_architect_agent() -> Agent:
    """Create an Architect agent for migration planning.
    
    Returns:
        Configured Architect agent with MigrationPlan output schema.
    """
    model = get_model()

    return Agent(
        name="Architect",
        role="Design the Nuxt.js migration plan",
        model=model,
        output_schema=MigrationPlan,
        instructions="""Based on the analysis, create a comprehensive MigrationPlan.
        
CRITICAL: You will receive a file list from the Analyzer. YOU MUST ONLY MIGRATE FILES THAT EXIST IN THAT LIST.
- Do NOT assume 'src/pages' exists if the analysis says 'src/app'.
- Do NOT include 'src/pages/Home.jsx' or other generic examples unless they are explicitly in the analysis.
- If the project uses Next.js App Router (src/app), your plan MUST target those specific files.
""",
    )
