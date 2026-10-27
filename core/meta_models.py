"""
Jenna AI OS — Meta Model API Integration

Integrates Meta's Muse Spark, Muse Voice Transcribe, Muse Image, and SAM 3.1
for the Meta Global AI Developer Hackathon (Oct 26 - Nov 4, 2026).

API docs: https://dev.meta.ai/docs
Models:
  - muse-spark-1.3: Reasoning/agent orchestration (Planner/Commander)
  - muse-voice-transcribe-1.0: Speech-to-text (voice pipeline)
  - muse-image-1.0: Image generation/understanding (Scholar/vision)
  - sam-3.1: Segmentation anything (vision pipeline)
"""
import os
from typing import Optional, Dict, Any, List
import httpx


class MetaModelAPI:
    """Client for Meta Model API (OpenAI-compatible)."""
    
    BASE_URL = "https://ai.meta.com/api/models"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("META_MODEL_API_KEY")
        if not self.api_key:
            raise ValueError("META_MODEL_API_KEY required (env or param)")
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=60.0)
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                              model: str = "muse-spark-1.3",
                              temperature: float = 0.7,
                              max_tokens: int = 4096) -> str:
        """Chat completion with Muse Spark."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def transcribe(self, audio_file: str) -> str:
        """Transcribe audio with Muse Voice Transcribe."""
        with open(audio_file, "rb") as f:
            files = {"file": ("audio.wav", f, "audio/wav")}
            data = {"model": "muse-voice-transcribe-1.0"}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.post(
                "/audio/transcriptions", data=data, files=files, headers=headers
            )
            response.raise_for_status()
            return response.json()["text"]
    
    async def generate_image(self, prompt: str, model: str = "muse-image-1.0") -> str:
        """Generate image with Muse Image."""
        payload = {
            "model": model,
            "prompt": prompt,
            "size": "1024x1024",
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.client.post("/images/generations", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["data"][0]["url"]
    
    async def segment(self, image_file: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Segment image with SAM 3.1."""
        with open(image_file, "rb") as f:
            files = {"image": ("image.png", f, "image/png")}
            data = {"model": "sam-3.1"}
            if prompt:
                data["prompt"] = prompt
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.post("/segmentation", data=data, files=files, headers=headers)
            response.raise_for_status()
            return response.json()


# ── Meta Model Tools for Agents ──────────────────────────────────────────

def create_meta_tools(api_key: Optional[str] = None):
    """Create Meta model tools for agent integration."""
    client = MetaModelAPI(api_key)
    
    async def meta_chat(messages: List[Dict[str, str]]) -> str:
        """Reason with Muse Spark for complex tasks."""
        return await client.chat_completion(messages)
    
    async def meta_transcribe(audio_file: str) -> str:
        """Transcribe audio using Muse Voice Transcribe."""
        return await client.transcribe(audio_file)
    
    async def meta_generate_image(prompt: str) -> str:
        """Generate image using Muse Image."""
        return await client.generate_image(prompt)
    
    async def meta_segment_image(image_file: str, prompt: str = "") -> Dict[str, Any]:
        """Segment image using SAM 3.1."""
        return await client.segment(image_file, prompt)
    
    return [
        {
            "name": "meta_chat",
            "description": "Reason with Muse Spark (Meta's advanced reasoning model)",
            "parameters": {
                "type": "object",
                "properties": {
                    "messages": {"type": "array", "description": "Chat messages"}
                },
                "required": ["messages"]
            },
            "function": meta_chat,
        },
        {
            "name": "meta_transcribe",
            "description": "Transcribe audio using Muse Voice Transcribe",
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_file": {"type": "string", "description": "Path to audio file"}
                },
                "required": ["audio_file"]
            },
            "function": meta_transcribe,
        },
        {
            "name": "meta_generate_image",
            "description": "Generate image using Muse Image",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image generation prompt"}
                },
                "required": ["prompt"]
            },
            "function": meta_generate_image,
        },
        {
            "name": "meta_segment_image",
            "description": "Segment image using SAM 3.1",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_file": {"type": "string", "description": "Path to image"},
                    "prompt": {"type": "string", "description": "Segmentation prompt (optional)"}
                },
                "required": ["image_file"]
            },
            "function": meta_segment_image,
        },
    ]
