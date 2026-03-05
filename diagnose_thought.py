import asyncio
import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def debug_call():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found")
        return

    client = genai.Client(api_key=api_key)
    
    tools = [{
        "name": "get_calendar_events",
        "description": "Recupera eventi dal calendario",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer"}
            }
        }
    }]
    
    function_declarations = [
        types.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=t["parameters"]
        ) for t in tools
    ]
    gemini_tools = [types.Tool(function_declarations=function_declarations)]
    
    config = types.GenerateContentConfig(
        tools=gemini_tools,
        temperature=0.0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    
    print("--- Turn 1: Asking for calendar ---")
    response = await client.aio.models.generate_content(
        model="gemini-flash-latest",
        contents="Che impegni ho oggi?",
        config=config
    )
    
    print(f"Status: {response.candidates[0].finish_reason}")
    for i, part in enumerate(response.candidates[0].content.parts):
        print(f"Part {i}: {type(part)}")
        if part.text:
            print(f"  Text: {part.text}")
        if part.function_call:
            print(f"  Function Call: {part.function_call.name}")
            print(f"  Args: {part.function_call.args}")
            # Check for thought signature or other attributes
            # Using dir() to see what's available
            print(f"  Available fields in part: {[f for f in dir(part) if not f.startswith('_')]}")
            if hasattr(part, 'thought'):
                print(f"  Thought detected: {part.thought}")
            
    # Try Turn 2 (replaying parts)
    if response.candidates[0].content.parts:
        parts_to_replay = response.candidates[0].content.parts
        
        # Simulate tool result
        tool_result = types.Part.from_function_response(
            name="get_calendar_events",
            response={"result": "Nessun impegno."}
        )
        
        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text="Che impegni ho oggi?")]),
            types.Content(role="model", parts=parts_to_replay),
            types.Content(role="user", parts=[tool_result])
        ]
        
        print("\n--- Turn 2: Sending tool result ---")
        try:
            response2 = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
                config=config
            )
            print(f"Response 2: {response2.text}")
        except Exception as e:
            print(f"Error in Turn 2: {e}")

if __name__ == "__main__":
    asyncio.run(debug_call())
