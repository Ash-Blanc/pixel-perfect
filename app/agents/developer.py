"""Developer agent for executing the migration with Nuxt MCP support."""

from agno.agent import Agent
from agno.tools.local_file_system import LocalFileSystemTools
from agno.tools.mcp import MCPTools
from agno.tools.models.morph import MorphTools
from agno.tools.shell import ShellTools

from app.config import get_model, key_manager


def create_developer_agent(base_dir: str = ".") -> Agent:
    """Create a Developer agent for executing migrations (sync version).
    
    Args:
        base_dir: Base directory for file system operations.
        
    Returns:
        Configured Developer agent.
    """
    # Set up file tools
    try:
        file_tools = LocalFileSystemTools(target_directory=base_dir)
    except TypeError:
        file_tools = LocalFileSystemTools()
    
    # Initialize tools with File system and Shell tools for scaffolding
    tools = [file_tools, ShellTools()]

    # Add Morph Tools if API key is available
    morph_key = key_manager.get_key("morph")
    if morph_key:
        morph_tools = MorphTools(api_key=morph_key)
        tools.append(morph_tools)

    model = get_model()

    instructions = """Implement the migration plan by converting files to Nuxt.js (Nuxt 4 target).

STEP 0: REALITY CHECK
- The Architect might have hallucinated files.
- Before converting ANY file, check if the source file actually exists in the file system.
- If the plan says to convert 'src/pages/Home.jsx' but it doesn't exist, SKIP IT and log a warning.

STEP 1: SCAFFOLDING (If starting fresh)
1. Check if the output directory exists and is empty.
2. If it needs scaffolding, use the `shell` tool to run: `npx nuxi@latest init <output_dir> --packageManager npm --gitInit false`
3. Verify that `nuxt.config.ts` and `package.json` are created.

STEP 2: MIGRATION execution
- Convert files to proper Nuxt 4 structure.
- PRIORITY: The migrated app MUST look exactly like the original.
- Preserve all CSS classes, styles, and Tailwind configurations precisely.
- Do not simplify or change the UI design.

STEP 3: VALIDATION (Self-Healing)
- After migration, run `npx nuxi typecheck` in the output directory.
- If errors are found, fix them immediately using the available tools.
- Ensure the project builds successfully.
"""
    if morph_key:
        instructions += "\nUse MorphTools for fast, intelligent code editing and generation when appropriate."

    return Agent(
        name="Developer",
        role="Execute the migration by writing Nuxt.js files",
        model=model,
        tools=tools,
        instructions=instructions,
    )


async def create_developer_agent_with_mcp(base_dir: str = ".") -> tuple[Agent, MCPTools]:
    """Create a Developer agent with Nuxt MCP for accurate code generation.
    
    Args:
        base_dir: Base directory for file system operations.
        
    Returns:
        Tuple of (Agent, MCPTools) - MCPTools must be closed when done.
    """
    # Connect to Nuxt MCP server for up-to-date Nuxt.js knowledge
    nuxt_mcp = MCPTools(
        url="https://nuxt.com/mcp",
        transport="streamable-http"
    )
    await nuxt_mcp.connect()

    # Set up file tools
    try:
        file_tools = LocalFileSystemTools(target_directory=base_dir)
    except TypeError:
        file_tools = LocalFileSystemTools()

    # Initialize tools with ShellTools for scaffolding
    tools = [file_tools, nuxt_mcp, ShellTools()]
    
    instructions = """Implement the migration plan by converting files to Nuxt.js (Nuxt 4 target).
    
STEP 0: REALITY CHECK
- The Architect might have hallucinated files.
- Before converting ANY file, check if the source file actually exists in the file system.
- If the plan says to convert 'src/pages/Home.jsx' but it doesn't exist, SKIP IT and log a warning.

STEP 1: SCAFFOLDING
- If the output directory is empty or missing, SCALFFOLD IT FIRST.
- Use the `shell` tool to run: `npx nuxi@latest init <output_dir> --packageManager npm --gitInit false`
- This ensures a valid Nuxt 4 project structure.

STEP 2: MIGRATION & PIXEL-PERFECT UI
- Implement the migration plan by converting files to Nuxt.js 4.
- CRITICAL: The migrated app MUST look exactly like the original.
- Preserve all CSS classes, style attributes, and Tailwind config exactly.
- Do not simplify the design or "clean up" styles unless necessary for Nuxt compatibility.
- Ensure all assets (images, fonts) are placed correctly in `public/` or `assets/`.

STEP 3: VALIDATION (Self-Healing)
- After major changes, run `npx nuxi typecheck` inside the output directory.
- If validation fails, ANALYZE the error and FIX it immediately.
- Do not ask for user permission to fix validation errors; simply fix them.

IMPORTANT: Use the Nuxt MCP tools to:
- Look up correct Nuxt.js 4 patterns and composables
- Verify component syntax and best practices
- Get accurate imports and module structures

Always generate idiomatic Nuxt.js 4 code with:
- <script setup> syntax
- defineProps/defineEmits for component APIs
- Proper Nuxt auto-imports (useFetch, useRoute, useState, etc.)
- Correct file conventions (pages/, components/, composables/)
"""

    # Add Morph Tools if API key is available
    morph_key = key_manager.get_key("morph")
    if morph_key:
        morph_tools = MorphTools(api_key=morph_key)
        tools.append(morph_tools)
        instructions += "\nUse MorphTools ('edit_file') for fast, intelligent code generation and refactoring."

    model = get_model()

    agent = Agent(
        name="Developer",
        role="Execute the migration by writing Nuxt.js files",
        model=model,
        tools=tools,
        instructions=instructions,
    )

    return agent, nuxt_mcp
