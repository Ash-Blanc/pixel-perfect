# Pixel Perfect: Next.js to Nuxt.js Migration Agent

<img width="1169" height="779" alt="image" src="https://github.com/user-attachments/assets/86d72923-413d-4ef3-8758-d86bbbee0529" />


Pixel Perfect is an advanced AI agent built with the Agno framework, designed to automate the conversion of Next.js applications to Nuxt.js. It analyzes an existing Next.js codebase (via GitHub URL) and reconstructs it as a high-quality, idiomatic Nuxt.js application, preserving styling and functionality.

## Features

- **Codebase Analysis**: Deeply analyzes Next.js project structure, dependencies, and component hierarchy.
- **Intelligent Mapping**: Maps React/Next.js patterns (Hooks, Context, Pages) to their Vue/Nuxt.js equivalents (Composables, Stores, Pages).
- **Pixel-Perfect Recreation**: Preserves styling (CSS Modules, Tailwind, Styled Components) to ensure the new app looks exactly like the original.
- **Automated Generation**: Generates the Nuxt.js project structure and files locally.
- **Agno Powered**: Utilizes Agno agents for orchestration, reasoning, and tool execution.

## Prerequisites

- **Python 3.10+**
- **uv**: A fast Python package installer and resolver.
- **Node.js & npm/pnpm/yarn**: For running the generated Nuxt.js application.

## Setup

1.  **Clone the repository:**
    ```bash
    gh repo clone Ash-Blanc/pixel-perfect
    cd pixel-perfect
    ```

2.  **Install with uv:**
    Install the tool globally using `uv`:
    ```bash
    uv tool install .
    ```

3.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and populate it with your API keys.
    ```bash
    cp .env.example .env
    ```
    
    You can also configure keys via the CLI:
    ```bash
    pixel-perfect config-key sk-proj-... openai
    ```

## Usage

### Running the Agent

Start the interactive migration wizard:

```bash
pixel-perfect migrate <github-repo-url> <output-directory>
```

Example:
```bash
pixel-perfect migrate https://github.com/example/nextjs-app ./nuxt-app
```

### Running Tests

This project uses **Scenario** for end-to-end testing.

```bash
uv run pytest tests/scenarios/
```

## Development

- **Prompts**: Managed via LangWatch. Use `langwatch prompt create <name>` and edit files in `prompts/`.
- **Agents**: Logic is located in `app/`.
- **Tests**: Add new scenario tests in `tests/scenarios/` for every new feature.

## Project Structure

- `app/`: Source code for the Agno agent.
- `prompts/`: Managed prompts.
- `tests/scenarios/`: End-to-end tests.
- `tests/evaluations/`: Jupyter notebooks for component evaluation.

## License

MIT
