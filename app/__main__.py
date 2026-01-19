"""
Main entry point for running the SurfSense application.

Run with: python -m app

Architecture:
- Layer 1: ConversationalAgent - user-facing dialogue management
- Layer 2: Contextual Layer - parking, accessibility, reviews, safety
- Layer 3: ForecastIntegrationAgent - forecast API integration
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import __version__
from app.core.logger import get_logger, setup_logging
from config.settings import get_settings, validate_startup_config


def print_banner() -> None:
    """Display the SurfSense welcome banner."""
    print("=" * 60)
    print("🏄 SurfSense - AI Surf Trip Planning Assistant")
    print("=" * 60)
    print("   Powered by a 3-layer agent architecture:")
    print("   • Conversational Agent (dialogue & personalization)")
    print("   • Contextual Layer (parking, safety, reviews)")
    print("   • Forecast Integration Agent (surf conditions)")


def print_config_summary(settings) -> None:
    """Display current configuration summary."""
    print(f"\n📋 Configuration Summary:")
    print(f"   LLM Provider: {settings.llm.provider}")
    print(f"   LLM Model: {settings.llm.model_name}")


async def chat_loop(settings) -> None:
    """
    Run the interactive chat loop using the agent architecture.

    Args:
        settings: Application settings.
    """
    from app.agents import ConversationalAgent, ForecastIntegrationAgent
    from app.core.llm_service import LLMService

    print("\n🏄 Initializing agents... (this may take a moment)")

    # Initialize LLM service
    try:
        llm_service = LLMService.from_settings(settings)
    except Exception as e:
        print(f"\n❌ Failed to load LLM: {e}")
        print("   Check your configuration and try again.")
        return

    # Initialize agents (Layer 1 and Layer 3)
    forecast_agent = ForecastIntegrationAgent()
    conversational_agent = ConversationalAgent(
        llm_service=llm_service,
        forecast_agent=forecast_agent
    )

    print("\n✅ Agents ready! Type 'quit' or 'exit' to leave.")
    print("   Commands: /forecast <spot>, /skill <level>, /reset")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye! Catch some waves!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye! Catch some waves!")
            break

        # Handle special commands
        if user_input.startswith("/"):
            await handle_command(user_input, conversational_agent, forecast_agent)
            continue

        # Process through conversational agent
        try:
            print("\n🤖 SurfSense: ", end="", flush=True)
            response = await conversational_agent.process(user_input)
            print(response)
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def handle_command(
    command: str,
    conv_agent: "ConversationalAgent",
    forecast_agent: "ForecastIntegrationAgent"
) -> None:
    """
    Handle special slash commands.
    
    Args:
        command: The command string (e.g., "/forecast Pipeline").
        conv_agent: The conversational agent.
        forecast_agent: The forecast integration agent.
    """
    parts = command[1:].split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "forecast":
        if not args:
            print("\n📊 Usage: /forecast <spot_name>")
            return
        print(f"\n📊 Fetching forecast for {args}...")
        try:
            result = await forecast_agent.get_forecast(args)
            print(f"\n   Spot: {result.get('spot', 'Unknown')}")
            print(f"   Source: {result.get('source', 'Unknown')}")
            print(f"   Forecasts: {result.get('forecast_count', 0)} points")
            if "forecasts" in result and result["forecasts"]:
                print("\n   Sample conditions:")
                for fc in result["forecasts"][:3]:
                    print(f"   • {fc.get('summary', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Error fetching forecast: {e}")

    elif cmd == "skill":
        if not args:
            current = conv_agent.get_user_preference("skill_level", "not set")
            print(f"\n🎯 Current skill level: {current}")
            print("   Usage: /skill <beginner|intermediate|advanced>")
            return
        level = args.lower()
        if level in ["beginner", "intermediate", "advanced"]:
            conv_agent.update_user_preference("skill_level", level)
            print(f"\n✅ Skill level set to: {level}")
        else:
            print("\n❌ Invalid skill level. Choose: beginner, intermediate, advanced")

    elif cmd == "reset":
        conv_agent.reset()
        print("\n🔄 Conversation reset. Starting fresh!")

    elif cmd == "help":
        print("\n📖 Available commands:")
        print("   /forecast <spot> - Get surf forecast")
        print("   /skill <level>   - Set your skill level")
        print("   /reset           - Reset conversation")
        print("   /help            - Show this help")

    else:
        print(f"\n❓ Unknown command: /{cmd}")
        print("   Type /help for available commands.")


def main() -> None:
    """Main application entry point."""
    print_banner()
    print(f"\nVersion: {__version__}")

    # Load and validate configuration
    try:
        settings = get_settings()

        # Setup logging (quieter for terminal chat)
        setup_logging(
            level="WARNING",  # Suppress info logs in chat mode
            log_format="text",
            log_file=settings.logging.file_path,
        )

        logger = get_logger(__name__)
        logger.info("SurfSense starting up", extra={"version": __version__})

        # Validate required keys (warning only in development)
        missing_keys = settings.validate_required_keys()
        if missing_keys:
            if settings.is_production():
                validate_startup_config()
            else:
                print(f"\n⚠️  Warning: Missing API keys: {', '.join(missing_keys)}")
                print("   Some features may not work.")

        print_config_summary(settings)

        # Start chat loop with async support
        asyncio.run(chat_loop(settings))

    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ Startup Error: {e}")
        print("   Check your .env file and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
