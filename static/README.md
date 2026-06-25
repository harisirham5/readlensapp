# ChatBot Assistant with OCR & Object Detection

A mobile-friendly ChatGPT-style web application with integrated OCR (Optical Character Recognition) and Object Detection capabilities.

## Features

✨ **ChatBot Interface**: Clean, modern chat interface similar to ChatGPT
- Chat history tracking with session management
- Real-time message streaming
- Light/Dark mode support

🔍 **Object Detection**: Identify and describe objects in images
- Upload images or use live camera
- AI-powered analysis using Moondream model

📝 **OCR (Text Recognition)**: Extract text from images
- Upload images or use live camera
- High-accuracy text detection using EasyOCR

📱 **Mobile-Optimized**: Fully responsive design
- Works on mobile phones, tablets, and desktops
- Touch-friendly interface
- Plus button for quick feature access

## Architecture

### Frontend
- **Framework**: Vanilla JavaScript (no dependencies)
- **Styling**: Modern CSS with responsive design
- **UI Pattern**: Modal-based feature selection

### Backend
- **Framework**: Flask (Python)
- **Models**:
  - **LLM**: Ollama with Mistral model for chatbot
  - **OCR**: EasyOCR for text recognition
  - **Vision**: Moondream for object detection
- **Storage**: In-memory chat history (session-based)

## Prerequisites

### System Requirements
- Python 3.8+
- Ollama installed and running
  - Mistral model: `ollama pull mistral`
  - Moondream model: `ollama pull moondream`
- Webcam (optional, for camera features)

### Python Dependencies
```bash
pip install flask opencv-python easyocr ollama numpy
```

## Installation

1. **Clone/Download the project**
```bash
cd "c:\Users\USER\Downloads\barang barang IDP\appproject"
```

2. **Install dependencies**
```bash
pip install flask opencv-python easyocr ollama numpy
```

3. **Ensure Ollama is running**
```bash
ollama serve
# In another terminal, pull required models:
ollama pull mistral
ollama pull moondream
```

4. **Start the Flask server**
```bash
python app.py
```

5. **Access the app**
- Open browser and go to: `http://localhost:5000`
- On mobile: Access from `http://<your-computer-ip>:5000`

## Usage

### Chat Mode (Default)
1. Type your message in the input field
2. Press Enter or click the up arrow to send
3. Chat history is automatically saved

### Image Analysis
1. Click the **+** button
2. Choose **Object Detection** or **OCR**
3. Select **Upload Image** or **Use Camera**
   - **Upload**: Select from your device gallery
   - **Camera**: Capture with your device camera
4. Click **Process** to analyze the image
5. Results appear in the chat history

### Clear Chat
Click the **🗑️** button in the header to clear chat history and start fresh

## API Endpoints

### POST `/chatbot`
Send a message to the chatbot
```json
{
  "message": "Your message here",
  "session_id": "optional_session_id"
}
```

### GET `/get_chat_history`
Retrieve chat history for a session
```
/get_chat_history?session_id=<session_id>
```

### POST `/process_image`
Process an image with OCR or Object Detection
```json
{
  "action": "ocr" or "object_detection",
  "image_source": "data:image/jpeg;base64,<image_data>",
  "session_id": "optional_session_id"
}
```

## Project Structure

```
appproject/
├── app.py                 # Flask backend
├── templates/
│   └── index.html         # Main UI (ChatGPT-style)
├── static/                # Static files (images, etc.)
├── tiny-yolov3.pt         # YOLOv3 model weights
├── download_model.py      # Model download utility
└── EasyOCR/               # EasyOCR library
```

## Configuration

### Change Port
In `app.py`, modify the last line:
```python
app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)  # Change port to 8000
```

### Change LLM Model
In `app.py` `/chatbot` route:
```python
response = ollama.chat(
    model='neural-chat',  # or 'dolphin-mixtral', 'llama2', etc.
    messages=[...]
)
```

### Disable Dark Mode
In `index.html`, remove or modify the `@media (prefers-color-scheme: dark)` CSS section

## Troubleshooting

### Camera Not Working
- Check browser permissions (Settings → Privacy → Camera)
- Ensure HTTPS or localhost access (some browsers require secure context)
- Try different browser (Chrome/Firefox recommended)

### Ollama Models Not Found
```bash
ollama list  # Check installed models
ollama pull mistral  # Install Mistral
ollama pull moondream  # Install Moondream
```

### Port Already in Use
```python
# In app.py, change port:
app.run(host='0.0.0.0', port=5001, ...)  # Use different port
```

### OCR Slow on First Run
EasyOCR downloads models on first use (~200MB). Subsequent runs are faster.

## Performance Tips

1. **Reduce Model Size**: Use smaller Ollama models for faster responses
2. **Enable GPU**: If available, Ollama will automatically use GPU
3. **Cache**: Chat history is cached in memory (clears on app restart)
4. **Image Size**: Smaller images process faster (resize before upload)

## Browser Support

✅ **Recommended**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

⚠️ **Limited Support**
- Safari on iOS (camera permissions may require additional steps)
- Internet Explorer (not supported)

## Security Notes

- App runs locally on `localhost:5000` by default
- Session IDs are randomly generated
- No external data transmission (all processing local)
- Change `app.secret_key` in production

## Future Enhancements

- [ ] Persistent database for chat history
- [ ] User authentication
- [ ] Image gallery history
- [ ] Settings/preferences panel
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Export chat as PDF/CSV

## License

This project uses open-source components:
- Flask - BSD License
- EasyOCR - Apache License 2.0
- OpenCV - Apache License 2.0
- Ollama - MIT License

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review console logs (F12 in browser)
3. Check server logs in terminal
4. Ensure all dependencies are installed

---

**Last Updated**: 2026-05-21
**Version**: 1.0
