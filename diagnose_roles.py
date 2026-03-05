import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def test_mapping(model_id, role_for_tool):
    client = genai.Client(api_key=api_key)
    
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text="Cosa ho in calendario?")]),
        types.Content(role="model", parts=[types.Part.from_function_call(
            name="get_calendar_events",
            args={"days": 3}
        )]),
        types.Content(role=role_for_tool, parts=[types.Part.from_function_response(
            name="get_calendar_events",
            response={"result": "Nessun evento trovato."}
        )])
    ]
    
    print(f"Testing {model_id} with role='{role_for_tool}'...")
    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=contents
        )
        print(f"SUCCESS {model_id}: {response.text}")
    except Exception as e:
        print(f"FAILURE {model_id}: {e}")

async def main():
    # Use models we know exist from previous list
    models = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
    for m in models:
        await test_mapping(m, "tool")
        await asyncio.sleep(1)
        await test_mapping(m, "user")
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
