# Gemini API Quickstart Guide

## Setup Instructions

### 1. Get Your Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Create a new API key (or use existing one)
4. Copy the key

### 2. Configure Environment Variables
1. Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```
2. Paste your API key into `.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Text Generation
```python
from gemini_helper import GeminiHelper

gemini = GeminiHelper()  # Uses GEMINI_API_KEY from .env
response = gemini.generate_text("What is Python?")
print(response)
```

### Image Analysis
```python
from gemini_helper import GeminiHelper

gemini = GeminiHelper()
response = gemini.analyze_image(
    "path/to/image.jpg",
    "What's in this image?"
)
print(response)
```

### Chat Conversation
```python
from gemini_helper import GeminiHelper

gemini = GeminiHelper()
messages = [
    {"role": "user", "content": "Hi, what's the capital of France?"},
    {"role": "user", "content": "Can you tell me about its history?"}
]
response = gemini.chat_conversation(messages)
print(response)
```

## Flask API Endpoints

### Text Generation Endpoint
```bash
curl -X POST http://localhost:5000/api/gemini/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'
```

### Image Analysis Endpoint
```bash
curl -X POST http://localhost:5000/api/gemini/analyze-image \
  -F "file=@path/to/image.jpg" \
  -F "prompt=What is in this image?"
```

## Available Models

- **gemini-pro**: Fast, efficient text generation
- **gemini-pro-vision**: Image analysis and understanding

## Key Features

✅ Text generation with adjustable creativity (temperature)  
✅ Image analysis from files or raw bytes  
✅ Multi-turn conversations  
✅ Easy Flask integration  
✅ Environment variable support  

## Troubleshooting

**Issue**: "GEMINI_API_KEY not provided"
- **Solution**: Make sure your `.env` file has `GEMINI_API_KEY=your_key`

**Issue**: Rate limiting errors
- **Solution**: Add delays between requests or upgrade your plan

**Issue**: Image analysis not working
- **Solution**: Ensure PIL is installed (`pip install Pillow`)

## Documentation
- [Google Generative AI Python SDK](https://ai.google.dev/tutorials/python_quickstart)
- [Gemini API Reference](https://ai.google.dev/docs)
