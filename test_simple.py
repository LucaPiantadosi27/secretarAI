import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def test_simple():
    client = genai.Client(api_key=api_key)
    try:
        # No tools, no system instruction, just a string
        print("Sending simple 'ping' to gemini-1.5-flash-latest...")
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents="ping"
        )
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
