"""
NVIDIA AI API Helper Module
Provides easy integration with NVIDIA NIM endpoints
"""

import os
from openai import OpenAI
from typing import Optional


class NvidiaHelper:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize NVIDIA API.

        Priority:
          1. Explicit argument (for programmatic use / tests)
          2. NVIDIA_API_KEY environment variable
          3. OPENAI_API_KEY environment variable (fallback)

        If no key is found, the helper is still constructed but every call
        will raise a clear RuntimeError pointing the user at the env var.
        """
        resolved = api_key or os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY")

        if not resolved:
            print(
                "WARNING: NVIDIA_API_KEY not set. NVIDIA-backed routes will return 503 "
                "until the key is provided. Set NVIDIA_API_KEY in your environment or .env."
            )

        # Empty string is treated as missing so a misconfigured env var does not
        # silently produce 401s that look like a code bug.
        self.api_key = resolved if (resolved and resolved.strip()) else None
        self.ready = self.api_key is not None

        # Default timeout so a hung network call does not block a request thread
        # indefinitely. Override via the `timeout` kwarg for slow vision calls.
        self.timeout = timeout

        if self.ready:
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key,
                timeout=self.timeout,
            )
        else:
            self.client = None

        self.model = 'meta/llama-3.1-8b-instruct'  # Fast text model
        self.vision_model = 'meta/llama-3.2-90b-vision-instruct'  # Vision model

    def _require_ready(self):
        if not self.ready:
            raise RuntimeError(
                "NVIDIA API key is not configured. Set NVIDIA_API_KEY in your "
                "environment and restart the server."
            )

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using NVIDIA model."""
        self._require_ready()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024
        )
        return response.choices[0].message.content

    def generate_vision_text(self, prompt: str, image_base64: str) -> str:
        """Analyze an image with Llama 3.2 Vision."""
        self._require_ready()
        if not image_base64:
            raise ValueError("image_base64 must be a non-empty base64 string")
        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content

    def chat_conversation(self, messages: list) -> str:
        """Have a multi-turn conversation with NVIDIA."""
        self._require_ready()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024
        )
        return response.choices[0].message.content

    def get_available_models(self) -> list:
        """Get list of available models."""
        return [
            'meta/llama-3.1-8b-instruct',
            'meta/llama-3.1-70b-instruct',
            'meta/llama-3.2-90b-vision-instruct',
            'nvidia/neva-22b'
        ]
