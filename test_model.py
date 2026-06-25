"""
Test Gemini 2.0 Flash model
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key found: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    print("\n✓ Testing text generation...")
    resp = model.generate_content("Say hello in one word")
    print(f"Response: {resp.text}")
    
    print("\n✓ Model configured successfully!")
else:
    print("❌ API key not found")
