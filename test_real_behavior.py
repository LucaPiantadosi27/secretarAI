import asyncio
import logging
import sys
from src.brain.orchestrator import BrainOrchestrator, Message, MAX_HISTORY_MESSAGES

# Configura il logging per vedere le protezioni in azione
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def test_real_behavior():
    print("\n=== TEST FUNZIONAMENTO REALE SECRETARAI ===\n")
    
    orchestrator = BrainOrchestrator()
    
    # --- TEST 1: TRIMMING HISTORY ---
    print(f"\n[1] Riempimento history oltre il limite ({MAX_HISTORY_MESSAGES} messaggi)...")
    for i in range(25):
        orchestrator.conversation_history.append(Message(role="user", content=f"Messaggio di test {i}"))
    
    print(f"DEBUG: Lunghezza history pre-elaborazione: {len(orchestrator.conversation_history)}")
    
    # Esegue un messaggio semplice (se l'API key non è valida, vedremo comunque il trimming nei log)
    print("\n[2] Invio messaggio per triggerare il trimming...")
    try:
        # Usiamo un timeout breve per non restare appesi se l'API risponde lentamente
        response = await orchestrator.process_message("Ciao, chi sei?")
        print(f"\nRisposta bot: {response}")
    except Exception as e:
        print(f"\nNota: La chiamata API ha restituito un errore (normale se non c'è una key valida), ma controlla i log sopra per il trimming.")
    
    print(f"\n[3] Verifica finale lunghezza history: {len(orchestrator.conversation_history)}")
    if len(orchestrator.conversation_history) <= MAX_HISTORY_MESSAGES + 2:
        print("✅ SUCCESS: La history è stata troncata correttamente.")
    else:
        print("❌ FAILURE: La history è ancora troppo lunga.")

    print("\n=== FINE TEST ===\n")

if __name__ == "__main__":
    asyncio.run(test_real_behavior())
