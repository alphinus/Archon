#!/usr/bin/env python3
"""AAL Validation Script

This script validates the Agent Abstraction Layer implementation by:
1. Loading the ProviderRegistry
2. Checking provider initialization
3. Validating provider configurations
4. Testing basic request execution (if API keys are available)

Run from Archon root directory:
    uv run python scripts/validate_aal.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aal.models import AgentRequest, AgentResponse
from aal.registry import get_provider_registry
from aal.service import get_agent_service


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


def validate_environment():
    """Check for required environment variables"""
    print_section("Environment Variables")

    api_keys = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }

    found_keys = []
    missing_keys = []

    for key, value in api_keys.items():
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print_success(f"{key}: {masked}")
            found_keys.append(key)
        else:
            print_warning(f"{key}: Not set")
            missing_keys.append(key)

    if not found_keys:
        print_error("No API keys found! AAL will not be able to execute requests.")
        return False

    if missing_keys:
        print_info(f"Optional API keys missing: {', '.join(missing_keys)}")

    return True


def validate_registry():
    """Validate the ProviderRegistry"""
    print_section("Provider Registry")

    try:
        registry = get_provider_registry()
        print_success("ProviderRegistry initialized")

        providers = registry.get_all_providers()

        if not providers:
            print_error("No providers loaded!")
            return None

        print_success(f"Loaded {len(providers)} provider(s)")

        for provider in providers:
            print(f"\n  📦 Provider: {provider.get_name()}")
            capabilities = provider.get_capabilities()
            print(f"     Capabilities: {', '.join(capabilities)}")

            # Check model configs
            if hasattr(provider, '_model_configs'):
                models = provider._model_configs
                print(f"     Models: {len(models)} configured")
                for model_name in list(models.keys())[:3]:  # Show first 3
                    print(f"       - {model_name}")

        return registry

    except Exception as e:
        print_error(f"Registry initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_service():
    """Validate the AgentService"""
    print_section("Agent Service")

    try:
        service = get_agent_service()
        print_success("AgentService initialized")

        if not service._providers:
            print_error("AgentService has no providers!")
            return None

        print_success(f"AgentService has {len(service._providers)} provider(s)")
        print_info(f"Providers: {', '.join(service._providers.keys())}")

        return service

    except Exception as e:
        print_error(f"AgentService initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_basic_request(service):
    """Test a basic AAL request (if API keys available)"""
    print_section("Test Request Execution")

    # Check if we have any API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not (has_anthropic or has_openai):
        print_warning("Skipping test request - no API keys available")
        return

    # Create a simple test request
    preferred_provider = "anthropic" if has_anthropic else "openai"

    test_request = AgentRequest(
        prompt="Say 'Hello from AAL!' in exactly 5 words.",
        preferred_provider=preferred_provider,
        max_tokens=50,
        temperature=0.0,
    )

    print_info(f"Sending test request to {preferred_provider}...")
    print(f"  Prompt: {test_request.prompt}")

    try:
        response: AgentResponse = await service.execute_request(test_request)

        if response.error:
            print_error(f"Request failed: {response.error}")
            return

        print_success("Request executed successfully!")
        print(f"\n  📝 Response Content:")
        print(f"     {response.content}")
        print(f"\n  📊 Metrics:")
        print(f"     Provider: {response.provider_used}")
        print(f"     Model: {response.model_name_used}")
        print(f"     Cost: ${response.cost_usd:.6f}")
        print(f"     Latency: {response.latency_ms}ms")
        print(f"     Tokens: {response.usage.get('input_tokens', 0)} in, "
              f"{response.usage.get('output_tokens', 0)} out")

    except Exception as e:
        print_error(f"Request execution failed: {e}")
        import traceback
        traceback.print_exc()


async def test_capability_routing(service):
    """Test capability-based routing"""
    print_section("Capability-Based Routing Test")

    # Check if we have any API keys
    has_any_key = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))

    if not has_any_key:
        print_warning("Skipping capability test - no API keys available")
        return

    # Test with specific capabilities
    test_request = AgentRequest(
        prompt="Test",
        required_capabilities=["text_generation", "quality_high"],
        max_tokens=10,
    )

    print_info("Testing request with capabilities: text_generation, quality_high")

    try:
        response = await service.execute_request(test_request)

        if response.error:
            print_warning(f"Capability routing test: {response.error}")
        else:
            print_success(f"Routed to: {response.provider_used} ({response.model_name_used})")
            print_info(f"Model has capabilities for high-quality text generation")

    except Exception as e:
        print_error(f"Capability routing test failed: {e}")


def print_summary(registry, service, env_ok):
    """Print validation summary"""
    print_section("Validation Summary")

    status = []

    if env_ok:
        status.append("✅ Environment variables configured")
    else:
        status.append("⚠️  Some environment variables missing")

    if registry:
        status.append(f"✅ ProviderRegistry loaded ({len(registry.get_all_providers())} providers)")
    else:
        status.append("❌ ProviderRegistry failed to load")

    if service:
        status.append(f"✅ AgentService initialized ({len(service._providers)} providers)")
    else:
        status.append("❌ AgentService failed to initialize")

    print("\n".join(status))

    overall_status = all([env_ok or registry, registry, service])

    print(f"\n{'='*60}")
    if overall_status:
        print("✅ AAL Validation PASSED")
    else:
        print("❌ AAL Validation FAILED")
    print(f"{'='*60}\n")

    return overall_status


async def main():
    """Main validation flow"""
    print("\n" + "="*60)
    print("  AI Empire HQ - AAL Validation Script")
    print("  Version: 1.0")
    print("="*60)

    # Step 1: Environment
    env_ok = validate_environment()

    # Step 2: Registry
    registry = validate_registry()

    # Step 3: Service
    service = validate_service()

    # Step 4: Test Request (if possible)
    if service:
        await test_basic_request(service)
        await test_capability_routing(service)

    # Summary
    success = print_summary(registry, service, env_ok)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
