import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def reproduce():
    client = genai.Client(api_key=api_key)
    
    # Simulate a history with a tool call and response
    # Correct roles: user -> model (function_call) -> user (function_response)
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text="Cosa ho in calendario")]),
        types.Content(role="model", parts=[types.Part.from_function_call(
            name="get_calendar_events",
            args={"days": 3}
        )]),
        types.Content(role="user", parts=[types.Part.from_function_response(
            name="get_calendar_events",
            response={"result": "Nessun evento trovato."}
        )])
    ]
    
    model_id = "gemini-1.5-flash"
    
    try:
        print(f"Testing {model_id} with role='user' for function_response...")
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=contents
        )
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
