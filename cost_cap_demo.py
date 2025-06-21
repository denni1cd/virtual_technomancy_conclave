"""
Demonstrates the cost cap enforcement for Technomancer and HighTechnomancer.
"""

import asyncio

from conclave.agents.agent_factory import factory
from conclave.agents.high_technomancer import HighTechnomancer
from conclave.services.cost_ledger import CostCapExceeded, log_and_check

async def demo_technomancer():
    """
    Instantiates a Technomancer and repeatedly calls its think() method 
    until the cost cap is exceeded.
    """
    print("--- Testing Technomancer Cost Cap ---")
    # This requires a real OpenAI key to be set in the environment
    # because it makes actual API calls.
    try:
        t = factory.spawn("Technomancer", goal="quick test")
        print(f"Created agent: {t.agent_id} with a cap of $10.00")
        
        # Consume budget
        for i in range(1, 15):
            print(f"Call {i}...")
            # The think method triggers the LLM call decorated by cost_guard
            await t.think("say hello")
            
    except CostCapExceeded as exc:
        print(f"\nSUCCESS: Cost cap exceeded as expected.\n{exc}")
    except Exception as exc:
        print(f"\nAn unexpected error occurred: {exc}")
        print("Please ensure your OPENAI_API_KEY is set in your environment.")


def demo_high_technomancer():
    """
    Instantiates a HighTechnomancer and repeatedly calls its deliberate() method 
    until the cost cap is exceeded.
    """
    print("\n--- Testing HighTechnomancer Cost Cap ---")
    try:
        ht = factory.spawn("HighTechnomancer", goal="deliberate test")
        print(f"Created agent: {ht.agent_id} with a cap of $25.00")

        # Consume budget by calling the decorated stub method
        for i in range(1, 150): # High cap needs more calls
            print(f"Call {i}...")
            # This is a stub and won't actually work on the spawned agent
            # ht.deliberate("continue")
            # For now, we manually log usage to test the cap
            log_and_check(ht.cfg.role_name, ht.agent_id, 1200, 0.18)


    except CostCapExceeded as exc:
        print(f"\nSUCCESS: Cost cap exceeded as expected.\n{exc}")
    except Exception as exc:
        print(f"An unexpected error occurred: {exc}")

if __name__ == "__main__":
    # Run HighTechnomancer demo (sync)
    demo_high_technomancer()
    
    # Run Technomancer demo (async)
    # Note: This will make real API calls and incur costs.
    asyncio.run(demo_technomancer())
    # print("\nTechnomancer demo is commented out to prevent unexpected API costs.")
    # print("Uncomment the line `asyncio.run(demo_technomancer())` to run it.") 