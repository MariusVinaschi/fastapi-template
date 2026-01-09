"""
Prefect worker entry point.
This module is used to deploy flows to Prefect.
"""
import asyncio

from app.workers.flows.example import example_flow, user_sync_flow


async def main():
    """
    Run example flows for testing.
    In production, flows are triggered via Prefect server.
    """
    print("Running example flow...")
    result = await example_flow()
    print(f"Example flow result: {result}")
    
    print("\nRunning user sync flow...")
    result = await user_sync_flow()
    print(f"User sync flow result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

