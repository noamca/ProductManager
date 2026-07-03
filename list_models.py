import google.generativeai as genai
import os

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    for m in genai.list_models():
        print(f"Name: {m.name} | Supported: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")
