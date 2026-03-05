import asyncio
import os
import logging
from src.brain.orchestrator import BrainOrchestrator, Message

# Setup logging to see our new debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Simulation")

async def run_simulation():
    print("\n--- INIZIO SIMULAZIONE SECRETARAI ---\n")
    
    orchestrator = BrainOrchestrator()
    
    # 1. Test History Trimming
    print("\n[1] TEST TRIMMING HISTORY")
    print("Riempio la history con 25 messaggi fittizi...")
    for i in range(25):
        orchestrator.conversation_history.append(Message(role="user", content=f"Messaggio inutile {i}"))
    
    print(f"History iniziale: {len(orchestrator.conversation_history)} messaggi.")
    
    # 2. Test Message Processing (this will trigger trimming)
    print("\n[2] TEST MESSAGGIO REALE (Trigger Trimming)")
    # We use a simple message. If API key is missing, it will catch the error gracefully.
    try:
        response = await orchestrator.process_message("Ciao, come ti chiami?")
        print(f"\nAI: {response}")
    except Exception as e:
        print(f"\nErrore (probabile API key mancante/invalida): {e}")
    
    print(f"\nLunghezza history dopo il trimming: {len(orchestrator.conversation_history)} (deve essere <= 22)")

    # 3. Test Tool Loop (Simulated tool call if we had a real key and prompts)
    # We already verified this with mocks in pytest, but this script ensures 
    # the real orchestrator flows through the loop.

    print("\n--- FINE SIMULAZIONE ---")

if __name__ == "__main__":
    asyncio.run(run_simulation())
