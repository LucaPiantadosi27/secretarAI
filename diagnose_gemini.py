import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

async def test_model(model_name):
    print(f"Testing model: {model_name}...")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents="Hello, identify yourself."
        )
        print(f"SUCCESS {model_name}: {response.text}")
        return True
    except Exception as e:
        print(f"FAILURE {model_name}: {e}")
        return False

async def main():
    models = [
        "gemini-1.5-flash-8b", 
        "gemini-1.5-flash", 
        "gemini-1.5-flash-latest",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite-preview-02-05", # New Lite 2.0
    ]
    results = {}
    for m in models:
        success = await test_model(m)
        results[m] = "SUCCESS" if success else "FAILURE"
        await asyncio.sleep(5) # Be gentle
    
    print("\n--- Summary ---")
    for m, res in results.items():
        print(f"{m}: {res}")

if __name__ == "__main__":
    asyncio.run(main())
