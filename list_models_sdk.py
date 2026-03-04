import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def main():
    client = genai.Client(api_key=api_key)
    try:
        models = client.models.list()
        for m in models:
            print(f"MODEL: {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
