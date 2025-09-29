
"""
Self-Extending Agents with Strands Meta-Tooling
"""
import os
import json

# Strands core components
from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.hooks import HookProvider, HookRegistry
from strands.experimental.hooks import BeforeToolInvocationEvent

from strands_tools import editor, shell

# Third-party imports
from colorama import Fore, init
from dotenv import load_dotenv


# Initialize colorama for color coding
init(autoreset=True)


# Color-coded logging hook for tool invocations before they are executed
class LoggingHook(HookProvider):
    """Logging hook for tool invocations. Logs details before a tool is invoked."""
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolInvocationEvent, self.log_start)

    def log_start(self, event: BeforeToolInvocationEvent) -> None:
        """Logs the tool invocation details."""
        print(f"{Fore.GREEN}{'='*60}")
        # Color-coded output for better visibility
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}🔧 TOOL INVOCATION")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Agent: {Fore.WHITE}{event.agent.name}")
        print(f"{Fore.BLUE}Tool: {Fore.WHITE}{event.tool_use['name']}")
        print(f"{Fore.MAGENTA}Input Parameters:")

        # Pretty print the input with color coding
        formatted_input = json.dumps(event.tool_use['input'], indent=2)
        for line in formatted_input.split('\n'):
            print(f"{Fore.WHITE}  {line}")

        print(f"{Fore.CYAN}{'='*60}")


# Color-coded agent response wrapper
def run_agent_with_colors(agent, prompt):
    """
    Run the agent with a prompt and display the response with color coding.
    This makes it easier to distinguish between different types of output.
    """
    print(f"Agent's current list of tools: {agent.tool_names}")
    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.YELLOW}🤖 AGENT REQUEST")
    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.CYAN}Prompt: {Fore.WHITE}{prompt}")
    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.YELLOW}📝 Agent Response:")
    print(f"{Fore.GREEN}{'='*80}")

    # Run the agent and capture the result
    result = agent(prompt)

    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.YELLOW}✅ AGENT RESPONSE COMPLETE")
    print(f"Agent's updated list of tools: {agent.tool_names}")
    print(f"{Fore.GREEN}{'='*80}")

    return result


# Load environment variables from the .env file
load_dotenv()


# Get Anthropic API key and model ID from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable.")

# Default to Claude 4 if not specified in environment variables
ANTHROPIC_MODEL_ID = os.getenv("ANTHROPIC_CLAUDE_4", "claude-sonnet-4-20250514")

CISCO_DEVICE_TYPE = os.getenv("DEVICE_TYPE", "cisco_xr")
CISCO_DEVICE_HOSTNAME = os.getenv("DEVICE_HOSTNAME")
CISCO_DEVICE_USERNAME = os.getenv("DEVICE_USERNAME")
CISCO_DEVICE_PASSWORD = os.getenv("DEVICE_PASSWORD")
CISCO_DEVICE_PORT = int(os.getenv("DEVICE_PORT"))


# Enable auto-approval for the file_write tool
os.environ["BYPASS_TOOL_CONSENT"] = "true"


# Configure Anthropic model
anthropic_model = AnthropicModel(
    client_args={
        "api_key": ANTHROPIC_API_KEY
    },
    # Set a generous max tokens limit for complex tool creation tasks
    max_tokens=8000,
    model_id=ANTHROPIC_MODEL_ID,
    params={
        "temperature": 1,

        # Enable "thinking" mode to help the model reason through complex tasks
        "thinking": {
            "type": "enabled",
            "budget_tokens": 1028  # Number of tokens allocated for thinking
        }
    }
)

# Define the system prompt to guide the agent's behavior

SYSTEM_PROMPT = f"""
You are a specialized network engineering agent capable of creating Python tools and using them to solve network challenges.

GOALS:
    - Create Python tools under cwd()/tools/*.py using the tool decorator
    - Each tool should be well-documented with clear docstrings and type hints
    - Use netmiko for network device connections (preferred over paramiko)
    - After writing a tool, you can use it immediately (hot-reloading enabled)
    - Create comprehensive unit tests for each tool under cwd()/tools/tests/test_*.py
    - Verify tests work by running them with pytest
    - Debug and fix any issues found during testing

NETWORK STANDARDS:
    - Follow organizational security policies
    - Use connection timeouts and error handling
    - Generate compliance reports in CSV format
    - Document all network changes and findings

TOOL TEMPLATE:
    from strands import tool

    @tool
    def tool_name(param1: type, param2: type) -> return_type:
        '''
        Clear description of what the tool does.
        
        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
            
        Returns:
            Description of return value
            
        Raises:
            ErrorType: When and why this error might occur
        '''
        # Implementation
        return result

Lab Environment Credentials:
    - Device Type: {CISCO_DEVICE_TYPE}
    - Device Hostname: {CISCO_DEVICE_HOSTNAME}
    - Device Username: {CISCO_DEVICE_USERNAME}
    - Device Password: {CISCO_DEVICE_PASSWORD}
    - Port: {CISCO_DEVICE_PORT}
    - Device Port: {CISCO_DEVICE_PORT}

NOTE: Use the new hot loaded tools and not the python files when testing the lab environment.
"""

# Create self-extending agent with Anthropic Claude 4

agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    model=anthropic_model,
    tools=[editor, shell],
    hooks=[LoggingHook()],

    # This is critical for self-extending functionality:
    # When set to True, the agent can dynamically load tools it creates
    # without restarting the runtime
    load_tools_from_directory=True
)

# Define the prompt for the agent
PROMPT = """
Create an interface description compliance tool for branch routers.

REQUIREMENTS:
  - All active interfaces must have descriptions
  - Descriptions must follow: <LOCATION>_<PEER>_<CIRCUIT-ID>
  - Example: "NYC_AWS_DIRECT_CKT123"
  - Identify interfaces status "up" or "down"

BUILD TOOLS TO:
  1. Connect to router via SSH
  2. Get interface list with descriptions
  3. Identify non-compliant interfaces
  4. Generate fix commands
  5. Create CSV report

Test with our lab router and document findings. 
"""

# Run the default prompt first
print(f"{Fore.GREEN}{'='*80}")
print(f"{Fore.YELLOW}🤖 Self-Extending Agent Demo")
print(f"{Fore.GREEN}{'='*80}")
print(f"{Fore.CYAN}Running default prompt to create and test tools...")
print(f"{Fore.GREEN}{'='*80}")

# Execute the default prompt
result = run_agent_with_colors(agent, PROMPT)

# Ask if user wants to continue with interactive mode
print(f"\n{Fore.GREEN}{'='*60}")
print(f"{Fore.YELLOW}🎯 Default Demo Complete!")
print(f"{Fore.GREEN}{'='*60}")
print(f"{Fore.CYAN}The agent has created and tested the requested tools.")
