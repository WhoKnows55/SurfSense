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
    from app.agents import ConversationalAgent, ContextualAgent, ForecastIntegrationAgent
    from app.core.llm_service import LLMService

    print("\n🏄 Initializing agents... (this may take a moment)")

    # Initialize LLM service
    try:
        llm_service = LLMService.from_settings(settings)
    except Exception as e:
        print(f"\n❌ Failed to load LLM: {e}")
        print("   Check your configuration and try again.")
        return

    # Initialize agents (Layer 1, Layer 2, and Layer 3)
    forecast_agent = ForecastIntegrationAgent()
    contextual_agent = ContextualAgent()
    conversational_agent = ConversationalAgent(
        llm_service=llm_service,
        forecast_agent=forecast_agent,
        contextual_agent=contextual_agent
    )

    print("\n✅ Agents ready! Type 'quit' or 'exit' to leave.")
    print("   Commands: /forecast, /assess, /windows, /trip, /context, /skill, /reset, /help")
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
            await handle_command(user_input, conversational_agent, forecast_agent, contextual_agent)
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
    forecast_agent: "ForecastIntegrationAgent",
    contextual_agent: "ContextualAgent"
) -> None:
    """
    Handle special slash commands.
    
    Args:
        command: The command string (e.g., "/forecast Pipeline").
        conv_agent: The conversational agent.
        forecast_agent: The forecast integration agent.
        contextual_agent: The contextual agent.
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

    elif cmd == "context":
        if not args:
            print("\n📍 Usage: /context <spot_name>")
            print("   Get parking, safety, reviews, and accessibility info.")
            return
        print(f"\n📍 Fetching context for {args}...")
        try:
            context = await contextual_agent.get_spot_context(args)
            print(contextual_agent.format_context_for_display(context))
        except Exception as e:
            print(f"\n❌ Error fetching context: {e}")

    elif cmd == "assess":
        # Parse: /assess <spot> [skill_level]
        arg_parts = args.split() if args else []
        if not arg_parts:
            print("\n🎯 Usage: /assess <spot_name> [skill_level]")
            print("   Assess conditions for your skill level.")
            print("   Example: /assess Pipeline intermediate")
            return
        
        spot = arg_parts[0]
        skill = arg_parts[1] if len(arg_parts) > 1 else conv_agent.get_user_preference("skill_level", "intermediate")
        
        print(f"\n🎯 Assessing conditions at {spot} for {skill} level...")
        try:
            result = await forecast_agent.assess_conditions(spot, skill, days=1)
            
            if "error" in result:
                print(f"\n❌ {result['error']}")
                return
            
            summary = result.get("summary", {})
            
            print(f"\n📊 Condition Assessment for {result.get('spot', spot)}")
            print(f"   Skill Level: {skill}")
            print(f"   Source: {result.get('source', 'Unknown')}")
            print(f"   Hours Assessed: {summary.get('total_hours', 0)}")
            print(f"   Average Score: {summary.get('average_score', 0)}/100")
            print(f"\n   📈 {summary.get('recommendation', 'No recommendation')}")
            
            # Best time
            best = summary.get("best_time", {})
            if best:
                rating_emoji = {"ideal": "🟢", "suitable": "🟡", "challenging": "🟠", "unsafe": "🔴"}.get(best.get("rating", ""), "⚪")
                print(f"\n   Best Time: {best.get('time', 'Unknown')}")
                print(f"   {rating_emoji} {best.get('rating', '').upper()} (Score: {best.get('score', 0)})")
                print(f"   {best.get('summary', '')}")
            
            # Rating breakdown
            breakdown = summary.get("rating_breakdown", {})
            if breakdown:
                print(f"\n   Rating Breakdown:")
                for rating, count in breakdown.items():
                    emoji = {"ideal": "🟢", "suitable": "🟡", "challenging": "🟠", "unsafe": "🔴"}.get(rating, "⚪")
                    print(f"      {emoji} {rating}: {count} hours")
            
            # Warnings
            warnings = summary.get("all_warnings", [])
            if warnings:
                print(f"\n   ⚠️  Warnings:")
                for w in warnings[:5]:
                    print(f"      • {w}")
                    
        except Exception as e:
            print(f"\n❌ Error assessing conditions: {e}")

    elif cmd == "windows":
        # Parse: /windows <spot> [skill_level] [days]
        arg_parts = args.split() if args else []
        if not arg_parts:
            print("\n🏄 Usage: /windows <spot_name> [skill_level] [days]")
            print("   Find optimal surf windows in the forecast.")
            print("   Example: /windows Pipeline intermediate 3")
            return
        
        spot = arg_parts[0]
        skill = arg_parts[1] if len(arg_parts) > 1 else conv_agent.get_user_preference("skill_level", "intermediate")
        days = int(arg_parts[2]) if len(arg_parts) > 2 else 3
        
        print(f"\n🏄 Finding surf windows at {spot} for {skill} level ({days} days)...")
        try:
            result = await forecast_agent.find_surf_windows(spot, skill, days)
            
            if "error" in result:
                print(f"\n❌ {result['error']}")
                return
            
            # Print the formatted display
            print(f"\n{result.get('display', 'No windows found')}")
            
        except Exception as e:
            print(f"\n❌ Error finding windows: {e}")

    elif cmd == "trip":
        # Parse: /trip <spot1,spot2,...> [skill_level] [days]
        arg_parts = args.split() if args else []
        if not arg_parts:
            print("\n🗺️  Usage: /trip <spot1,spot2,spot3> [skill_level] [days]")
            print("   Plan a multi-day surf trip across multiple spots.")
            print("   Example: /trip Pipeline,Waikiki,Sunset intermediate 3")
            print("   Separate spots with commas (no spaces).")
            return
        
        spots_str = arg_parts[0]
        spot_names = [s.strip() for s in spots_str.split(",")]
        
        if len(spot_names) < 1:
            print("\n❌ Please specify at least one spot.")
            return
        
        skill = arg_parts[1] if len(arg_parts) > 1 else conv_agent.get_user_preference("skill_level", "intermediate")
        days = int(arg_parts[2]) if len(arg_parts) > 2 else 3
        
        print(f"\n🗺️  Planning {days}-day trip to {', '.join(spot_names)} for {skill} level...")
        print("   Fetching forecasts and optimizing itinerary...")
        
        try:
            result = await forecast_agent.plan_trip(spot_names, skill, days)
            
            if "error" in result:
                print(f"\n❌ {result.get('message', result['error'])}")
                return
            
            # Print the formatted display
            print(f"\n{result.get('display', 'Failed to generate itinerary')}")
            
        except Exception as e:
            print(f"\n❌ Error planning trip: {e}")

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
        print("   /assess <spot> [skill] - Assess conditions for skill level")
        print("   /windows <spot> [skill] [days] - Find optimal surf windows")
        print("   /trip <spot1,spot2,...> [skill] [days] - Plan multi-day trip")
        print("   /context <spot>  - Get parking, safety, reviews, accessibility")
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
