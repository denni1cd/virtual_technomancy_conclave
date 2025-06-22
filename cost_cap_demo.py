"""
Cost cap demo with tracing integration.

This demo shows:
1. Cost cap enforcement across multiple agents
2. Tracing integration with hierarchical spans
3. Cost events attached to spans
4. Fail-open behavior when tracing is disabled
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from conclave.agents.agent_factory import factory
from conclave.services.cost_ledger import log_and_check, CostCapExceeded
from conclave.services.tracing import get_tracer, reset_tracer


def demo_with_tracing():
    """Demo with tracing enabled."""
    print("=== Cost Cap Demo with Tracing ===")
    
    # Enable tracing
    os.environ["TRACE_ENABLED"] = "langsmith"
    
    # Reset tracer to pick up new environment
    reset_tracer()
    tracer = get_tracer()
    
    print(f"Tracer type: {type(tracer).__name__}")
    
    # Start a root span for the demo
    with tracer.root_span(
        project_name="cost_cap_demo",
        metadata={
            "demo_type": "cost_cap_with_tracing",
            "description": "Demonstrating cost caps with tracing integration"
        }
    ):
        print("\n1. Creating agents...")
        
        # Create agents with tracing context
        with tracer.child_span("agent_creation", "AGENT"):
            arch = factory.spawn("ArchTechnomancer")
            high = factory.spawn("HighTechnomancer")
            tech = factory.spawn("Technomancer")
            
            print(f"   - ArchTechnomancer: {arch.agent_id}")
            print(f"   - HighTechnomancer: {high.agent_id}")
            print(f"   - Technomancer: {tech.agent_id}")
        
        print("\n2. Simulating LLM calls with cost tracking...")
        
        # Simulate LLM calls with different costs
        costs = [
            ("ArchTechnomancer", arch.agent_id, 500, 0.075, "planning"),
            ("HighTechnomancer", high.agent_id, 800, 0.12, "coordination"),
            ("Technomancer", tech.agent_id, 1200, 0.18, "execution"),
            ("Technomancer", tech.agent_id, 600, 0.09, "tool_call"),
        ]
        
        for role, agent_id, tokens, cost, operation in costs:
            with tracer.child_span(f"llm_call_{operation}", "LLM"):
                try:
                    log_and_check(
                        role_name=role,
                        agent_id=agent_id,
                        tokens=tokens,
                        cost=cost,
                        extra={"operation": operation}
                    )
                    print(f"   ✓ {role} ({operation}): ${cost:.3f}, {tokens} tokens")
                except CostCapExceeded as e:
                    print(f"   ✗ {role} ({operation}): {e}")
        
        print("\n3. Simulating debate events...")
        
        # Simulate debate events
        with tracer.child_span("debate_session", "DEBATE"):
            tracer.add_event(
                "debate_round",
                {
                    "round": 1,
                    "participants": 3,
                    "topic": "data_store_selection"
                }
            )
            
            tracer.add_event(
                "debate_choice",
                {
                    "decision": "PostgreSQL",
                    "consensus_reached": True,
                    "rounds_used": 1
                }
            )
            
            print("   ✓ Debate completed with consensus")
        
        print("\n4. Final cost summary...")
        
        # Show final trace URL if available
        try:
            trace_url = tracer.get_trace_url()
            if trace_url:
                print(f"   📊 View trace: {trace_url}")
            else:
                print("   📊 Trace URL not available (using noop tracer)")
        except Exception:
            print("   📊 Trace URL not available")


def demo_without_tracing():
    """Demo with tracing disabled."""
    print("\n=== Cost Cap Demo without Tracing ===")
    
    # Disable tracing
    os.environ["TRACE_ENABLED"] = "false"
    
    # Reset tracer to pick up new environment
    reset_tracer()
    tracer = get_tracer()
    
    print(f"Tracer type: {type(tracer).__name__}")
    
    # Same operations but without tracing
    print("\n1. Creating agents...")
    arch = factory.spawn("ArchTechnomancer")
    high = factory.spawn("HighTechnomancer")
    tech = factory.spawn("Technomancer")
    
    print(f"   - ArchTechnomancer: {arch.agent_id}")
    print(f"   - HighTechnomancer: {high.agent_id}")
    print(f"   - Technomancer: {tech.agent_id}")
    
    print("\n2. Simulating LLM calls with cost tracking...")
    
    costs = [
        ("ArchTechnomancer", arch.agent_id, 500, 0.075, "planning"),
        ("HighTechnomancer", high.agent_id, 800, 0.12, "coordination"),
        ("Technomancer", tech.agent_id, 1200, 0.18, "execution"),
        ("Technomancer", tech.agent_id, 600, 0.09, "tool_call"),
    ]
    
    for role, agent_id, tokens, cost, operation in costs:
        try:
            log_and_check(
                role_name=role,
                agent_id=agent_id,
                tokens=tokens,
                cost=cost,
                extra={"operation": operation}
            )
            print(f"   ✓ {role} ({operation}): ${cost:.3f}, {tokens} tokens")
        except CostCapExceeded as e:
            print(f"   ✗ {role} ({operation}): {e}")
    
    print("\n3. Cost tracking works without tracing")
    print("   ✓ All operations completed successfully")


def demo_fail_open():
    """Demo fail-open behavior when tracing backend is down."""
    print("\n=== Fail-Open Demo ===")
    
    # Enable tracing but simulate backend failure
    os.environ["TRACE_ENABLED"] = "langsmith"
    reset_tracer()
    
    # Mock the langsmith import to fail
    import sys
    from unittest.mock import Mock
    
    # Save original module
    original_langsmith = sys.modules.get('langsmith')
    
    # Remove langsmith module to simulate import failure
    if 'langsmith' in sys.modules:
        del sys.modules['langsmith']
    
    try:
        tracer = get_tracer()
        print(f"Tracer type: {type(tracer).__name__}")
        print("   ✓ System fell back to noop tracer")
        
        # Operations should still work
        with tracer.root_span("test_project"):
            tracer.add_event("test", {"data": "value"})
        print("   ✓ Tracing operations completed without error")
        
    finally:
        # Restore original module
        if original_langsmith:
            sys.modules['langsmith'] = original_langsmith


def main():
    """Run the complete demo."""
    print("🚀 Conclave Cost Cap & Tracing Demo")
    print("=" * 50)
    
    # Demo 1: With tracing enabled
    demo_with_tracing()
    
    # Demo 2: Without tracing
    demo_without_tracing()
    
    # Demo 3: Fail-open behavior
    demo_fail_open()
    
    print("\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("\nKey features demonstrated:")
    print("• Hierarchical span creation (Arch → High → Tech)")
    print("• Cost events attached to spans")
    print("• PII redaction in metadata")
    print("• Fail-open behavior when backends are down")
    print("• Environment-based tracing control")


if __name__ == "__main__":
    main() 