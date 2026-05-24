from dotenv import load_dotenv
from google import genai
import os

load_dotenv()
api_key = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello and something to ecourage me to work",
)
print(response.text)
