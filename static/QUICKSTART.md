# Quick Start Guide - ChatBot Assistant App

## ⚡ Fast Setup (5 minutes)

### Step 1: Ensure Ollama is Running
```bash
ollama serve
# Keep this terminal open
```

### Step 2: Open New Terminal & Install Dependencies
```bash
cd "c:\Users\USER\Downloads\barang barang IDP\appproject"
pip install flask opencv-python easyocr ollama numpy
```

### Step 3: Start the App
```bash
python app.py
```

You should see:
```
Initializing AI models. This may take a moment...
Loading EasyOCR model...
Ollama LLaVA integration ready.
Initialization complete. Starting server...
WARNING in app.run(), use app.run_simple() if the automatic reloading is not working...
```

### Step 4: Access the App
- **Desktop**: Open browser → `http://localhost:5000`
- **Mobile**: Find your computer IP and go to `http://<YOUR-IP>:5000`

> To find your computer IP:
> - **Windows**: Run `ipconfig` in PowerShell, look for IPv4 Address (e.g., 192.168.1.100)

---

## 📱 Using the App

### Chat Mode
1. Type a message in the input field at the bottom
2. Press **Enter** or click the **↑** arrow
3. Wait for AI response
4. Repeat!

### Analyze Images
1. Click the **+** button (left of chat input)
2. Choose **Object Detection** or **OCR**
3. Select **Upload Image** or **Use Camera**
   - **Upload**: Browse your device files
   - **Camera**: Snap a photo with your device camera
4. Click **Process**
5. Results show in chat

### Clear Chat
Click the **🗑️** trash icon to start fresh

---

## 🛠️ Common Issues & Fixes

### "Connection refused" or "Cannot connect"
- **Fix**: Make sure Flask is running (you should see server logs in terminal)
- Check that Ollama is also running in another terminal

### Camera doesn't work
- **Fix**: 
  - Check browser permissions (look for camera icon in address bar)
  - Try Chrome instead of Safari/Edge
  - Ensure running on `localhost` or HTTPS (some browsers require this)

### Ollama models not found
- **Fix**: In terminal, run:
```bash
ollama pull mistral
ollama pull moondream
```

### Takes too long to respond
- **Fix**: 
  - First run of OCR takes longer (downloads ~200MB)
  - Mistral model takes 5-30 seconds per response
  - Try uploading smaller images

### Port 5000 already in use
- **Fix**: Edit last line in `app.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)  # Use 5001
```

---

## 💡 Tips

### Best Practices
- ✅ Use natural language (e.g., "Tell me about this object")
- ✅ Upload clear, well-lit images for best OCR
- ✅ Use mobile camera for better real-time capture
- ✅ Keep images reasonably sized (< 5MB)

### For Better Responses
Change the LLM model in `app.py` line ~60:
```python
model='neural-chat'  # Faster, good quality
# or
model='dolphin-mixtral'  # Slower, best quality
# or
model='llama2'  # Balanced
```

---

## 📊 Architecture at a Glance

```
Your Browser/Phone
    ↓
Frontend (HTML/CSS/JS)
    ↓
Flask Backend (Python)
    ↓
AI Models
  ├─ Mistral (LLM for chat)
  ├─ EasyOCR (text recognition)
  └─ Moondream (object detection)
```

---

## 🚀 What's Next?

- [x] Chat with AI
- [x] Upload images for analysis
- [x] Use camera to capture images
- [x] Extract text with OCR
- [x] Identify objects with AI
- [ ] Add user login (optional)
- [ ] Save chat to database (optional)
- [ ] Deploy to cloud (optional)

---

## 📝 Session Management

Each chat session has a unique ID:
- Your chat history is saved during the session
- Click 🗑️ to clear and start new session
- Refresh page = new session (loses history)
- History clears when app restarts

---

## 🔒 Privacy & Security

✅ **Fully Local**: All processing happens on your computer
✅ **No Cloud**: No data sent to external servers
✅ **No Tracking**: No analytics or data collection
✅ **Open Source**: All models and code are open-source

---

## 📞 Need Help?

1. Check terminal for error messages
2. Look in browser console (F12 → Console tab)
3. Ensure all dependencies are installed: `pip list`
4. Try restarting Ollama: `ollama serve`
5. Check README.md for detailed troubleshooting

---

## 🎯 Quick Commands

```bash
# Start Ollama (Terminal 1)
ollama serve

# Download models
ollama pull mistral
ollama pull moondream

# Install dependencies
pip install flask opencv-python easyocr ollama numpy

# Run app (Terminal 2)
python app.py

# Find your IP (Windows)
ipconfig

# Access app
http://localhost:5000  # Local
http://192.168.1.100:5000  # Remote device
```

---

**You're all set! 🎉 Enjoy your ChatBot Assistant app!**
