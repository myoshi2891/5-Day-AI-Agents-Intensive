from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from google.genai import types


def print_evaluation_guide() -> None:
    """Display evaluation results analysis guide."""
    print("📊 Understanding Evaluation Results:")
    print()
    print("🔍 EXAMPLE ANALYSIS:")
    print()
    print("Test Case: living_room_light_on")
    print("  ❌ response_match_score: 0.45/0.80")
    print("  ✅ tool_trajectory_avg_score: 1.0/1.0")
    print()
    print("📈 What this tells us:")
    print("• TOOL USAGE: Perfect - Agent used correct tool with correct parameters")
    print("• RESPONSE QUALITY: Poor - Response text too different from expected")
    print("• ROOT CAUSE: Agent's communication style, not functionality")
    print()
    print("🎯 ACTIONABLE INSIGHTS:")
    print("1. Technical capability works (tool usage perfect)")
    print("2. Communication needs improvement (response quality failed)")
    print("3. Fix: Update agent instructions for clearer language or constrained response.")
    print()


# Configure Model Retry on errors
retry_config = types.HttpRetryOptions(
    attempts=3,  # Maximum retry attempts
    exp_base=2,  # Delay multiplier (standard exponential backoff)
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

def set_device_status(location: str, device_id: str, status: str) -> dict:
    """Sets the status of a smart home device.

    Args:
        location: The room where the device is located.
        device_id: The unique identifier for the device.
        status: The desired status, either 'ON' or 'OFF'.

    Returns:
        A dictionary confirming the action.
    """
    print(f"Tool Call: Setting {device_id} in {location} to {status}")
    return {
        "success": True,
        "message": f"Successfully set the {device_id} in {location} to {status.lower()}."
    }

# This agent has DELIBERATE FLAWS that we'll discover through evaluation!
root_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="home_automation_agent",
    description="An agent to control smart devices in a home.",
    instruction="""You are a home automation assistant. You control ALL smart devices in the house.

    You have access to lights, security systems, ovens, fireplaces, and any other device the user mentions.
    Always try to be helpful and control whatever device the user asks for.

    When users ask about device capabilities, tell them about all the amazing features you can control.""",
    tools=[set_device_status],
)


if __name__ == "__main__":
    print_evaluation_guide()
