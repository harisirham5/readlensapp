# Gemini API Complete Setup Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Get Your API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key" button
3. Select "Create API key in new project" (or existing project)
4. Copy your API key

### Step 2: Configure Your Environment
```bash
# Copy the example file
cp .env.example .env

# Edit .env and paste your API key
# On Windows, you can use Notepad:
notepad .env
```

Your `.env` should look like:
```
GEMINI_API_KEY=your_actual_api_key_here
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this
```

### Step 3: Install Dependencies
```bash
# Make sure you're in your virtual environment if using one
pip install -r requirements.txt
```

### Step 4: Test the Setup
```bash
# Run the quickstart examples
python gemini_quickstart_examples.py
```

If successful, you should see responses from Gemini!

---

## 📚 Usage Guide

### Option A: Direct Python Usage

```python
from gemini_helper import GeminiHelper

# Initialize
gemini = GeminiHelper()  # Uses GEMINI_API_KEY from .env

# Text Generation
response = gemini.generate_text("Explain Python in 2 sentences")
print(response)

# Image Analysis
response = gemini.analyze_image("path/to/image.jpg", "What's in this image?")
print(response)

# Multi-turn Chat
messages = [
    {"role": "user", "content": "What is AI?"},
    {"role": "user", "content": "How is it used in healthcare?"}
]
response = gemini.chat_conversation(messages)
print(response)
```

### Option B: Flask API (Web Service)

Start the Flask server:
```bash
python app.py
```

Then make HTTP requests:

**1. Text Generation**
```bash
curl -X POST http://localhost:5000/api/gemini/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Machine Learning?", "temperature": 0.7}'
```

**2. Chat**
```bash
curl -X POST http://localhost:5000/api/gemini/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"},
      {"role": "user", "content": "What can you do?"}
    ]
  }'
```

**3. Image Analysis**
```bash
curl -X POST http://localhost:5000/api/gemini/analyze-image \
  -F "file=@/path/to/image.jpg" \
  -F "prompt=Describe this image"
```

**4. OCR + Gemini Analysis**
```bash
curl -X POST http://localhost:5000/api/gemini/analyze-ocr-with-gemini \
  -H "Content-Type: application/json" \
  -d '{"image_source": "data:image/jpeg;base64,...", "prompt": "Analyze this text"}'
```

**5. Check Status**
```bash
curl http://localhost:5000/api/gemini/status
```

### Test Script

Run the automated test suite:
```bash
python test_gemini_api.py
```

---

## 🎯 Common Tasks

### Generate Creative Content
```python
gemini = GeminiHelper()
poem = gemini.generate_text(
    "Write a short poem about AI",
    temperature=0.9  # Higher = more creative
)
```

### Analyze Documents (OCR + Analysis)
```python
# This uses readlens integration
# Performs OCR then sends to Gemini for analysis
gemini.analyze_image("document.jpg", "Summarize this document")
```

### Temperature Control
- **0.0-0.3**: Deterministic, factual (good for data extraction)
- **0.5-0.7**: Balanced (good for most tasks)
- **0.8-1.0**: Creative (good for brainstorming, writing)

---

## 🔒 Security Best Practices

1. **Never commit your API key**
   - Always use `.env` file (it's in `.gitignore`)
   - Keep `.env.example` without the actual key

2. **Use environment variables**
   ```python
   import os
   api_key = os.getenv('GEMINI_API_KEY')
   ```

3. **Protect your keys in production**
   - Use secrets management systems
   - Never log API keys
   - Rotate keys periodically

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY not provided"
**Solution:** Check that your `.env` file exists and contains a valid key
```bash
cat .env  # View the file
```

### "Connection timeout" or "API error"
**Solution:** 
- Check your internet connection
- Verify API key is valid
- Check you haven't exceeded rate limits

### "No module named 'google'"
**Solution:** Reinstall dependencies
```bash
pip install --upgrade google-generativeai
```

### "Image analysis not working"
**Solution:** Ensure Pillow is installed
```bash
pip install Pillow
```

### Rate Limiting
If you get rate limit errors:
- Add delays between requests
- Check your plan at [Google AI Studio](https://aistudio.google.com)
- Upgrade to a higher tier if needed

---

## 📊 Monitoring & Limits

### Current Free Tier Limits:
- 60 requests per minute
- Image analysis supported
- Text and vision models available

Check your usage in [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## 🚀 Integration Examples

### With readlens Integration
The `gemini_helper` is already integrated into your Flask app:

```python
# The app auto-initializes Gemini if GEMINI_API_KEY is set
# Available at: /api/gemini/* endpoints
```

### Real-time Image Processing
```python
# Combine with your camera feed
frame = capture_frame()  # Your camera logic
analysis = gemini.analyze_image_from_bytes(
    frame.tobytes(),
    "What's happening in this scene?"
)
```

---

## 📖 References

- [Google Generative AI Documentation](https://ai.google.dev/docs)
- [Gemini API Reference](https://ai.google.dev/api)
- [Python SDK Repository](https://github.com/google/generative-ai-python)

---

## ✅ Verification Checklist

- [ ] API key obtained from Google AI Studio
- [ ] `.env` file created with API key
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test examples run successfully
- [ ] Flask server starts without errors
- [ ] API endpoints respond correctly

---

**You're all set!** Start using Gemini in your project. 🎉
