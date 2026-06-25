"""
Gemini API Helper Module
Provides easy integration with Google's Gemini AI models
"""

import google.generativeai as genai
import os
from typing import Optional

class GeminiHelper:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini API with your API key.
        
        Args:
            api_key: Your Google Gemini API key. If None, looks for GEMINI_API_KEY env variable
        """
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not provided. Pass it directly or set it as an environment variable."
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text using Gemini Pro model.
        
        Args:
            prompt: The text prompt to send to Gemini
            temperature: Controls randomness (0.0-1.0). Higher = more creative
            
        Returns:
            Generated text response
        """
        response = self.model.generate_content(prompt)
        return response.text
    
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Analyze an image using Gemini Vision model.
        
        Args:
            image_path: Path to the image file
            prompt: The prompt/question about the image
            
        Returns:
            Analysis text response
        """
        import PIL.Image
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image = PIL.Image.open(image_path)
        response = self.vision_model.generate_content([prompt, image])
        return response.text
    
    def analyze_image_from_bytes(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> str:
        """
        Analyze an image from raw bytes.
        
        Args:
            image_bytes: Raw image bytes
            prompt: The prompt/question about the image
            mime_type: MIME type of the image
            
        Returns:
            Analysis text response
        """
        response = self.vision_model.generate_content([
            {
                "mime_type": mime_type,
                "data": image_bytes
            },
            prompt
        ])
        return response.text
    
    def chat_conversation(self, messages: list) -> str:
        """
        Have a multi-turn conversation with Gemini.
        
        Args:
            messages: List of dicts with 'role' and 'content' keys
                     role: 'user' or 'assistant'
                     content: the message text
            
        Returns:
            Latest assistant response
        """
        chat = self.model.start_chat()
        
        for message in messages:
            role = "user" if message['role'] == 'user' else 'model'
            chat.send_message(message['content'])
        
        return chat.history[-1].parts[0].text if chat.history else ""
    
    def get_available_models(self) -> list:
        """Get list of available Gemini models"""
        models = genai.list_models()
        return [m.name for m in models]
