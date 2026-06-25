"""
Gemini API Quickstart Examples
Simple examples to get started with Gemini API
"""

from gemini_helper import GeminiHelper
import os

# Initialize Gemini Helper (will use GEMINI_API_KEY from .env)
gemini = GeminiHelper()

print("=" * 60)
print("Gemini API Quickstart Examples")
print("=" * 60)

# Example 1: Simple text generation
print("\n[Example 1] Simple Text Generation")
print("-" * 60)
response = gemini.generate_text("What are the top 3 benefits of Python?")
print(f"Q: What are the top 3 benefits of Python?\n")
print(f"A: {response}\n")

# Example 2: Creative text with higher temperature
print("[Example 2] Creative Content Generation")
print("-" * 60)
creative_response = gemini.generate_text(
    "Write a short, funny haiku about debugging code",
    temperature=0.9
)
print(f"Haiku:\n{creative_response}\n")

# Example 3: Multi-turn conversation
print("[Example 3] Multi-turn Conversation")
print("-" * 60)
messages = [
    {"role": "user", "content": "What is machine learning?"},
    {"role": "user", "content": "Can you give me a practical example?"}
]
conversation = gemini.chat_conversation(messages)
print(f"Conversation Response:\n{conversation}\n")

# Example 4: Available models
print("[Example 4] Available Models")
print("-" * 60)
models = gemini.get_available_models()
print("Available Gemini Models:")
for model in models[:5]:  # Show first 5
    print(f"  - {model}")

print("\n" + "=" * 60)
print("✓ All examples completed successfully!")
print("=" * 60)
