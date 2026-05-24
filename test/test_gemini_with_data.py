from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import json

load_dotenv()
api_key = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=(
        "You are scoring event relevance for a user.\n"
        "User profile: 3rd-year ECE student, embedded/firmware focus, Auckland.\n"
        'Event: "Web3 NFT Hackathon - Build a JPEG marketplace, $500 prize, online."\n'
        'Respond with JSON: {"score": <1-10>, "reasoning": "<one sentence>"}'
    ),
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)
result = json.loads(response.text)
print(json.dumps(result, indent=2))
