
"""
Self-Extending Agents with Strands Meta-Tooling

This script demonstrates how to create a self-extending agent using the Strands Agents framework.
A self-extending agent can write and use new tools during runtime, effectively expanding its own capabilities as needed.

The agent can:
1. Generate new tools based on natural language descriptions
2. Test and debug its own creations
3. Immediately use the tools it creates

Prerequisites:
- An Anthropic API key (Claude 4 model recommended)
- Python 3.8+ environment
- Basic understanding of Python and LLM agents
"""
import os

# Strands core components
from strands import Agent

# Tools that allow the agent to interact with the file system and shell
from strands_tools import editor, shell

# Claude model integration
from strands.models.anthropic import AnthropicModel

# Hooks for logging tool invocations
from strands.hooks import HookProvider, HookRegistry
from strands.experimental.hooks import BeforeToolInvocationEvent

# Color coding for better visibility
from colorama import Fore, Back, Style, init

from dotenv import load_dotenv

# Initialize colorama for color coding
init(autoreset=True)  # Automatically reset colors after each print


# Color-coded logging hook for tool invocations before they are executed
class LoggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolInvocationEvent, self.log_start)

    def log_start(self, event: BeforeToolInvocationEvent) -> None:
        # Color-coded output for better visibility
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}🔧 TOOL INVOCATION")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Agent: {Fore.WHITE}{event.agent.name}")
        print(f"{Fore.BLUE}Tool: {Fore.WHITE}{event.tool_use['name']}")
        print(f"{Fore.MAGENTA}Input Parameters:")
        
        # Pretty print the input with color coding
        import json
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
    print(f"{Fore.GREEN}{'='*80}")
    
    return result


# Load environment variables from the .env file
# This allows secure storage of API keys and configuration
load_dotenv()


# Get Anthropic API key and model ID from environment variables
# These should be defined in your .env file as:
# ANTHROPIC_API_KEY=your_api_key_here
# ANTHROPIC_CLAUDE_4=claude-sonnet-4-20250514 (or your preferred model version)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable.")

# Default to Claude 4 if not specified in environment variables
ANTHROPIC_MODEL_ID = os.getenv("ANTHROPIC_CLAUDE_4", "claude-sonnet-4-20250514")

# Enable auto-approval for the file_write tool
# This bypasses prompts asking for permission when the agent wants to write files
# IMPORTANT: For production use, you may want to disable this for security reasons
os.environ["BYPASS_TOOL_CONSENT"] = "true"


# Configure Anthropic model
# For self-extending agents, we recommend using Claude 4 with thinking enabled
# The "thinking" parameter allows the model to work through complex problems step by step
anthropic_model = AnthropicModel(
    client_args={
        "api_key": ANTHROPIC_API_KEY
    },
    # Set a generous max tokens limit for complex tool creation tasks
    max_tokens=8000,
    model_id=ANTHROPIC_MODEL_ID,
    params={
        # Temperature of 1.0 encourages more creative responses
        # For more deterministic behavior, you can lower this value
        "temperature": 1,
        
        # Enable "thinking" mode to help the model reason through complex tasks
        # This significantly improves the quality of generated tools
        "thinking": {
            "type": "enabled",
            "budget_tokens": 1028  # Number of tokens allocated for thinking
        }
    }
)

# Define the system prompt to guide the agent's behavior
# This prompt is critical as it provides instructions to the agent on:
# 1. What it should create (Python tools)
# 2. Where to store them (tools directory)
# 3. How to test them (unit tests with pytest)
# 4. What to do if tests fail (debug and fix)

SYSTEM_PROMPT = """
You are a specialized agent capable of creating Python tools and using them to solve problems.

Goal:
    - Create Python tools under cwd()/tools/*.py using the tool decorator
    - Each tool should be well-documented with clear docstrings and type hints
    - After writing a tool, you can use it immediately (hot-reloading enabled)
    - Create comprehensive unit tests for each tool under cwd()/tools/tests/test_*.py
    - Verify tests work by running them with pytest
    - Debug and fix any issues found during testing

Process for each tool:
    1. Design the tool function with appropriate parameters and return types
    2. Implement the tool with robust error handling and documentation
    3. Create test cases covering normal usage and edge cases
    4. Run tests to verify functionality
    5. Use the tool to solve the specified problem
    6. Document your approach and results

Tool template:
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

Directory structure:
    - tools/            # Main directory for all tools
      - __init__.py     # Make it a proper package
      - tool_name.py    # One file per tool
      - tests/          # Directory for all tests
        - __init__.py   # Make it a proper package
        - test_tool_name.py  # One test file per tool
"""

# Create self-extending agent with Anthropic Claude 4
# This agent will be able to:
# 1. Create new Python tools
# 2. Test these tools
# 3. Debug and fix any issues
# 4. Use the tools immediately after creation

agent = Agent(
    system_prompt=SYSTEM_PROMPT,  # The instructions we defined earlier
    model=anthropic_model,        # The Claude 4 model we configured
    tools=[editor, shell],        # Tools for file operations and shell commands
    hooks=[LoggingHook()],        # Hooks for color-coded logging of tool invocations
    
    # This is critical for self-extending functionality:
    # When set to True, the agent can dynamically load tools it creates
    # without restarting the runtime
    load_tools_from_directory=True
)

print(f"List of tools available to the agent: {agent.tool_names}")

# Define the prompt for the agent
# This prompt asks the agent to create multiple tools and solve specific problems
# It includes clear expectations for testing and demonstration

prompt = """
I need you to create several Python tools to solve the following problems:

1. Create a tool named 'add_numbers' that adds two numbers, then use it to add 5 and 7.

2. Create a tool named 'calculate_compound_interest' that calculates compound interest with parameters for principal, rate, time, and compounding frequency. Use it to find the final value of $1000 invested at 5% annual interest for 3 years, compounded quarterly.

3. Create a tool named 'analyze_text' that takes a text string and returns statistics including: word count, character count, average word length, and most frequent word. Use it to analyze this sample text: "The quick brown fox jumps over the lazy dog. The fox was quick and brown and very clever."

For each tool:
1. Create the tool in the proper directory
2. Create comprehensive unit tests
3. Run the tests using pytest and ensure they pass
4. Show the tool in action by solving the specified problem
5. Provide the exact result of using the tool

After creating all tools, summarize which tools you've created, which tests were run, and all the results obtained.
"""

# Test the color coding system
def test_color_coding():
    """Test the color coding system to ensure it's working properly."""
    print(f"{Fore.GREEN}Testing color coding system...")
    print(f"{Fore.RED}Red text for errors")
    print(f"{Fore.GREEN}Green text for success")
    print(f"{Fore.YELLOW}Yellow text for warnings")
    print(f"{Fore.BLUE}Blue text for information")
    print(f"{Fore.MAGENTA}Magenta text for highlights")
    print(f"{Fore.CYAN}Cyan text for separators")
    print(f"{Fore.WHITE}White text for normal content")
    print(f"{Fore.GREEN}{'='*50}")
    print(f"{Fore.YELLOW}Color coding test complete!")
    print(f"{Fore.GREEN}{'='*50}")


# Run the default prompt first
print(f"{Fore.GREEN}{'='*80}")
print(f"{Fore.YELLOW}🤖 Self-Extending Agent Demo")
print(f"{Fore.GREEN}{'='*80}")
print(f"{Fore.CYAN}Running default prompt to create and test tools...")
print(f"{Fore.GREEN}{'='*80}")

# Execute the default prompt
result = run_agent_with_colors(agent, prompt)

# Ask if user wants to continue with interactive mode
print(f"\n{Fore.GREEN}{'='*60}")
print(f"{Fore.YELLOW}🎯 Default Demo Complete!")
print(f"{Fore.GREEN}{'='*60}")
print(f"{Fore.CYAN}The agent has created and tested the requested tools.")
print(f"Agent new current list of tools: {agent.tool_names}")
print(f"{Fore.WHITE}Would you like to continue with interactive mode? (y/n): ", end="")

continue_interactive = input().strip().lower()

if continue_interactive in ['y', 'yes']:
    # Interactive loop to query the self-extending agent
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"{Fore.YELLOW}🤖 Interactive Mode")
    print(f"{Fore.GREEN}{'='*60}")
    print(f"{Fore.CYAN}Welcome to interactive mode!")
    print(f"{Fore.WHITE}Type 'exit' or 'quit' to end the session.")
    print(f"{Fore.WHITE}Type 'test' to test the color coding system.")
    print(f"{Fore.BLUE}Example queries:")
    print(f"{Fore.WHITE}- Create a tool to add two numbers")
    print(f"{Fore.WHITE}- Create a tool to fetch weather data")
    print(f"{Fore.WHITE}- Create a tool to send a message")
    print(f"{Fore.WHITE}- Create a tool to calculate compound interest")
    print(f"{Fore.GREEN}{'='*60}")

    while True:
        query = input(f"\n{Fore.YELLOW}User> {Fore.WHITE}").strip()

        if query == "":
            continue

        if query.lower() in ["exit", "quit"]:
            print(f"\n{Fore.GREEN}Goodbye!")
            break
        
        if query.lower() == "test":
            test_color_coding()
            continue
        
        # Use the color-coded wrapper for agent interactions
        run_agent_with_colors(agent, query)
else:
    print(f"\n{Fore.GREEN}Demo complete! Goodbye!")
