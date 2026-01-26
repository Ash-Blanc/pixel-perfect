"""CLI entry point for the Pixel-Perfect Migration Agent using cli2."""

import asyncio
import os
import sys

# making it compatible for non-linux systems
if os.name == 'nt' and 'HOME' not in os.environ:
    os.environ['HOME'] = os.environ.get('USERPROFILE','')
    
import cli2

# Ensure app package is importable when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.team import get_migration_team, get_migration_team_with_mcp
from app.tools import run_shell_command
from app import cli_config


# Create CLI group
cli = cli2.Group(doc="""
Pixel-Perfect: Next.js to Nuxt.js Migration Agent

Automatically migrate your Next.js applications to Nuxt.js with AI-powered
analysis, planning, and code generation.

Commands:
  migrate        - Migrate a Next.js app to Nuxt.js
  analyze        - Analyze a Next.js project
  config-show    - Show current configuration
  config-provider - Set AI provider
  config-key     - Add API key
  config-model   - Set model
  version        - Show version info
""")


# --- Config Commands ---

@cli.cmd(name="config-show")
def config_show():
    """Show current configuration."""
    cfg = cli_config.show_config()
    print(f"Provider: {cfg['provider']}")
    print(f"Model: {cfg['model']}")
    print(f"Config file: {cfg['config_file']}")
    print()
    print("API Keys:")
    for provider, keys in cfg['api_keys'].items():
        if keys:
            print(f"  {provider}: {', '.join(keys)}")
    if not any(cfg['api_keys'].values()):
        print("  (none configured)")
    print()
    print("Supported providers:", ", ".join(cli_config.SUPPORTED_PROVIDERS.keys()))


@cli.cmd(name="config-provider")
def config_provider(provider: str):
    """
    Set the AI provider to use.

    :param provider: Provider name (mistral, openai, anthropic, google, groq, deepseek)
    """
    if cli_config.set_provider(provider):
        print(f"✓ Provider set to: {provider}")
        print(f"  Default model: {cli_config.get_model(provider)}")
    else:
        print(f"✗ Unknown provider: {provider}")
        print(f"  Supported: {', '.join(cli_config.SUPPORTED_PROVIDERS.keys())}")


@cli.cmd(name="config-key")
def config_key(key: str, provider: str = None):
    """
    Add API key(s) for a provider. Supports comma-separated keys for load balancing.

    :param key: The API key(s) to add (can be comma-separated)
    :param provider: Provider name (defaults to current provider)
    """
    provider = provider or cli_config.get_provider()
    if cli_config.add_api_key(key, provider):
        keys = [k.strip() for k in key.split(",") if k.strip()]
        if len(keys) > 1:
            print(f"✓ Added {len(keys)} keys for {provider}")
        else:
            masked = f"{keys[0][:8]}...{keys[0][-4:]}" if len(keys[0]) > 12 else "***"
            print(f"✓ Added key for {provider}: {masked}")
    else:
        print(f"✗ Failed to add key for {provider}")


@cli.cmd(name="config-clear")
def config_clear(provider: str = None):
    """
    Clear all API keys for a provider.

    :param provider: Provider name (defaults to current provider)
    """
    provider = provider or cli_config.get_provider()
    cli_config.clear_api_keys(provider)
    print(f"✓ Cleared all keys for {provider}")


@cli.cmd(name="config-model")
def config_model(model: str, provider: str = None):
    """
    Set the model to use for a provider.

    :param model: Model ID (e.g., gpt-4o, claude-sonnet-4-5)
    :param provider: Provider name (defaults to current provider)
    """
    provider = provider or cli_config.get_provider()
    cli_config.set_model(model, provider)
    print(f"✓ Model for {provider} set to: {model}")


# --- Session Commands ---

@cli.cmd(name="session-list")
def session_list():
    """List past migration sessions."""
    from app.config import get_database
    from app.cli_config import CONFIG_DIR
    import sqlite3
    
    db_path = CONFIG_DIR / "storage.db"
    
    if not db_path.exists():
        print("No sessions found (database does not exist).")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='team_sessions'")
        if not cursor.fetchone():
             # Try legacy 'sessions' table or just report empty
             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
             if not cursor.fetchone():
                 print("No sessions found.")
                 conn.close()
                 return
             table = "sessions"
        else:
             table = "team_sessions"

        cursor.execute(f"SELECT session_id, created_at, updated_at FROM {table} ORDER BY updated_at DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No sessions found.")
            return

        print(f"{'SESSION ID':<36} | {'LAST UPDATED':<20}")
        print("-" * 60)
        for row in rows:
            # row is a tuple
            sid, created, updated = row
            # Agno sometimes stores timestamps as floats or ints
            print(f"{sid:<36} | {updated}")
            
    except Exception as e:
        print(f"Error listing sessions: {e}")
        print("Note: If this is a new installation, no sessions may exist yet.")


@cli.cmd(name="session-resume")
def session_resume(session_id: str, repo: str, output: str):
    """
    Resume a specific session. Requires repo and output paths context.
    
    :param session_id: The Session ID to resume
    :param repo: Original repo path/URL
    :param output: Output directory
    """
    migrate(repo=repo, output=output, session_id=session_id)


# --- Migration Commands ---

async def _migrate_with_mcp(source_path: str, output_dir: str, session_id: str = None):
    """Run migration with Nuxt MCP for accurate code generation."""
    team, nuxt_mcp = await get_migration_team_with_mcp(base_dir=os.getcwd(), session_id=session_id)

    prompt = f"""
    I want to migrate the Next.js application located at '{source_path}' to a Nuxt.js application at '{output_dir}'.
    
    Please follow this process:
    1. Analyzer: List and analyze the files in '{source_path}'.
    2. Architect: Create a MigrationPlan for converting to Nuxt.js in '{output_dir}'.
    3. Developer: Execute the plan and write the new files.
       Use the Nuxt MCP tools to look up correct patterns and best practices.
    """
    
    # If resuming, we might want to skip the prompt or change it?
    # For now, if session_id is present, we still send the prompt but valid session context will be there.
    # Actually, if resuming, user might just want to continue.
    
    input_text = prompt if not session_id else None

    try:
        # Use interactive CLI app for multi-turn conversation
        if session_id:
            print(f"Resuming session: {session_id}")
            # When resuming, typically we don't send a massive prompt again, 
            # we just enter the loop. But we need to connect first.
            await team.acli_app(input=input_text, stream=True)
        else:
            await team.acli_app(input=prompt, stream=True)
    finally:
        await nuxt_mcp.close()


@cli.cmd
def migrate(repo: str, output: str, mcp: bool = True, session_id: str = None):
    """
    Migrate a Next.js application to Nuxt.js.

    :param repo: GitHub repository URL or local path to the Next.js app
    :param output: Output directory for the generated Nuxt.js app
    :param mcp: Use Nuxt MCP for accurate code generation (default: True)
    :param session_id: Resume a previous session by ID
    """
    # Ensure output directory exists
    output_dir = os.path.abspath(output)
    
    # Safety Check: Warn if directory exists and is not empty (and not resuming)
    if os.path.exists(output_dir) and os.listdir(output_dir) and not session_id:
        print(f"WARNING: Output directory '{output_dir}' is not empty.")
        # Simple confirmation if interactive, or just warn
        # Since we use cli2, we can't easily prompt unless we add a library.
        # For now, just a strong warning is good.
        print("Existing files may be overwritten.")
        
    os.makedirs(output_dir, exist_ok=True)

    source_path = os.path.abspath(repo)
    if repo.startswith("http"):
        repo_name = repo.split("/")[-1].replace(".git", "")
        temp_dir = f"tmp/clones/{repo_name}"
        # Only clone if not resuming, or ensure it exists?
        # If resuming, maybe the temp dir is gone? 
        # For simplicity, we re-clone if needed.
        if not os.path.exists(temp_dir):
            print(f"Cloning {repo} to {temp_dir}...")
            run_shell_command(f"git clone {repo} {temp_dir}")
        source_path = os.path.abspath(temp_dir)

    print(f"Starting migration from {source_path} to {output_dir}...")
    print(f"Using provider: {cli_config.get_provider()}")

    if mcp:
        print("Using Nuxt MCP for accurate code generation...")
        asyncio.run(_migrate_with_mcp(source_path, output_dir, session_id))
    else:
        # Sync version without MCP
        team = get_migration_team(base_dir=os.getcwd(), session_id=session_id)
        if session_id:
            print(f"Resuming session: {session_id}")
            team.cli_app(input=None, stream=True)
        else:
            prompt = f"""
            I want to migrate the Next.js application located at '{source_path}' to a Nuxt.js application at '{output_dir}'.
            
            Please follow this process:
            1. Analyzer: List and analyze the files in '{source_path}'.
            2. Architect: Create a MigrationPlan for converting to Nuxt.js in '{output_dir}'.
            3. Developer: Execute the plan and write the new files.
            """
            team.cli_app(input=prompt, stream=True)


@cli.cmd
def analyze(repo: str):
    """
    Analyze a Next.js project structure without migrating.

    :param repo: Path to the Next.js application to analyze
    """
    from app.agents import create_analyzer_agent

    source_path = os.path.abspath(repo)
    if not os.path.exists(source_path):
        print(f"Error: Path '{source_path}' does not exist")
        return

    print(f"Analyzing {source_path}...")
    
    # Analyzer uses a separate DB or transient? 
    # Usually single-shot, but we can make it persist if needed.
    analyzer = create_analyzer_agent(base_dir=source_path)
    analyzer.print_response(
        f"Analyze the Next.js project at '{source_path}'. List all files, identify the framework version, dependencies, and key architectural patterns.",
        stream=True
    )


@cli.cmd
def version():
    """Show the version of pixel-perfect."""
    print("pixel-perfect v0.2.0")
    print(f"  Provider: {cli_config.get_provider()}")
    print(f"  Model: {cli_config.get_model()}")
    print("  Nuxt MCP: enabled")


def main():
    """Entry point for the CLI."""
    cli.entry_point()


if __name__ == "__main__":
    main()