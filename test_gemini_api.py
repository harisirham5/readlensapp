"""
Flask routes testing script for Gemini API endpoints
Test the Flask API endpoints locally
"""

import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("Gemini API Flask Endpoints Tester")
print("=" * 60)

# Test 1: Check Gemini Status
print("\n[Test 1] Check Gemini API Status")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/gemini/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Generate text
print("\n[Test 2] Generate Text")
print("-" * 60)
try:
    payload = {
        "prompt": "What is Python used for?",
        "temperature": 0.7
    }
    response = requests.post(
        f"{BASE_URL}/api/gemini/generate",
        json=payload
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Prompt: {payload['prompt']}")
    print(f"\nResponse: {result.get('response', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Chat conversation
print("\n[Test 3] Chat Conversation")
print("-" * 60)
try:
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, what can you help me with?"},
            {"role": "user", "content": "Can you explain quantum computing?"}
        ]
    }
    response = requests.post(
        f"{BASE_URL}/api/gemini/chat",
        json=payload
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {result.get('response', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Analyze image with Gemini
print("\n[Test 4] Analyze Image (requires image file)")
print("-" * 60)
try:
    # You would need to provide an actual image file
    # This is just an example of how to call it
    image_path = "path/to/your/image.jpg"
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'prompt': 'What is in this image?'}
            response = requests.post(
                f"{BASE_URL}/api/gemini/analyze-image",
                files=files,
                data=data
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Skipped - no image file found at {image_path}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("✓ Testing completed!")
print("=" * 60)
