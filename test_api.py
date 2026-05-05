import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "say hello"}],
        max_tokens=5
    )
    print("API Key is VALID")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"API Key is INVALID or error occurred: {e}")
