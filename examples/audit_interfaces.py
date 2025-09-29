
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

TOOL_CALLS = 0

# Color-coded logging hook for tool invocations before they are executed
class LoggingHook(HookProvider):
    """Logging hook for tool invocations. Logs details before a tool is invoked."""
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolInvocationEvent, self.log_start)

    def log_start(self, event: BeforeToolInvocationEvent) -> None:
        """Logs the tool invocation details."""
        global TOOL_CALLS
        TOOL_CALLS += 1
        print(f"{Fore.GREEN}{'='*60}")
        # Color-coded output for better visibility
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}🔧 TOOL INVOCATION")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Agent: {Fore.WHITE}{event.agent.name}")
        print(f"{Fore.BLUE}Tool: {Fore.WHITE}{event.tool_use['name']}")
        print(f"{Fore.MAGENTA}Input Parameters:")

        # Pretty print the input with color coding, masking passwords
        input_data = event.tool_use['input'].copy()
        if 'password' in input_data:
            input_data['password'] = "********"
        
        formatted_input = json.dumps(input_data, indent=2)
        for line in formatted_input.split('\n'):
            print(f"{Fore.WHITE}  {line}")

        print(f"{Fore.CYAN}{'='*60}")


# Color-coded agent response wrapper
def run_agent_with_colors(agent, prompt):
    """
    Run the agent with a prompt and display the response with color coding.
    This makes it easier to distinguish between different types of output.
    """
    print("Agent's current list of tools:")
    for tool in agent.tool_names:
        print(f"{Fore.WHITE}  - {tool}")
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
    print(f"{Fore.YELLOW}✅ AGENT RESPONSE COMPLETE\n")
    print("Agent's updated list of tools:")
    for tool in agent.tool_names:
        print(f"{Fore.WHITE}  - {tool}")
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
You are a network automation expert that creates Python tools to solve network challenges.

CAPABILITIES:
- Create Python tools under tools/*.py using the @tool decorator
- Tools are HOT-RELOADED automatically after creation - you can call them directly by name
- You have access to netmiko for device connections

CRITICAL INSTRUCTION:
After creating a tool with @tool decorator, it becomes immediately available as a callable tool.
DO NOT run tools using shell/python commands. Use them directly as tools.
IF YOU RUN THE TOOL AND IT FAILS DUE TO NETMIKO NOT INSTALLED, INSTALL IT FIRST. THEN RUN THE TOOL AGAIN.

❌ WRONG: shell("python tools/check_compliance.py")
❌ WRONG: shell("cd tools && python router_connection.py")
✅ CORRECT: check_compliance(hostname="{CISCO_DEVICE_HOSTNAME}")
✅ CORRECT: router_connection(host="{CISCO_DEVICE_HOSTNAME}")

WORKFLOW:
1. Understand the requirement
2. Create tool using editor with @tool decorator
3. Call the tool directly by its function name (it's now available!)
4. Show the results

TOOL TEMPLATE:
    from strands import tool
    
    @tool
    def tool_name(param: type) -> return_type:
        '''Brief description.
        
        Args:
            param: What this parameter does
            
        Returns:
            What this returns
        '''
        # Implementation
        return result

After writing this to tools/tool_name.py, you can immediately call:
tool_name(param=value)

LAB DEVICE:
- Type: {CISCO_DEVICE_TYPE}
- Host: {CISCO_DEVICE_HOSTNAME}
- Username: {CISCO_DEVICE_USERNAME}
- Password: {CISCO_DEVICE_PASSWORD}
- Port: {CISCO_DEVICE_PORT}

IMPORTANT REMINDERS:
1. Tools created with @tool decorator are immediately available - no import needed
2. Never use shell to execute Python files - use the tool directly
3. The tool function name (not the filename) is what you call
4. Pass parameters directly to the tool function

Example: If you create tools/check_interfaces.py with function check_interfaces(),
you use it by calling: check_interfaces(host="{CISCO_DEVICE_HOSTNAME}")
NOT by running: shell("python tools/check_interfaces.py") nor cd tools && python -c .....
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
Create a tool to check if router interfaces have proper descriptions.

Requirements:
- Connect to our lab router via SSH  
- Check all interfaces for descriptions
- Flag any without the pattern: LOCATION_PEER_CIRCUIT
- Generate a fix list

Use the tools to get the results.
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
print(f"{Fore.CYAN}Total tool calls: {TOOL_CALLS}")