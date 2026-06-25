"""
Check available NVIDIA AI models
"""
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('NVIDIA_API_KEY')
if not api_key:
    print("❌ NVIDIA_API_KEY not found in .env")
    exit(1)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

print("Available NVIDIA Models:")
print("=" * 60)

try:
    models = client.models.list()
    for model in models.data:
        print(f"\nModel Name: {model.id}")
except Exception as e:
    print(f"Error fetching models: {e}")
