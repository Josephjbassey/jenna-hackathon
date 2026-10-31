"""
Meta Model API Skills for Jenna Agents
Provides tools for Muse Spark, Muse Voice, Muse Image, and SAM 3.1
"""
import os
import httpx
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from config import META_MODEL_API_BASE, META_MODEL_API_KEY


class MetaModelClient:
    """Client for Meta Model API (OpenAI-compatible)."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or META_MODEL_API_KEY
        self.base_url = base_url or META_MODEL_API_BASE
        if not self.api_key:
            raise ValueError("META_MODEL_API_KEY required")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                              model: str = "muse-spark-1.3",
                              temperature: float = 0.7,
                              max_tokens: int = 4096) -> str:
        """Chat completion with Muse Spark or other Meta models."""
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


# Global client instance
_meta_client: Optional[MetaModelClient] = None

def get_meta_client() -> MetaModelClient:
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaModelClient()
    return _meta_client


@tool
async def meta_reason(messages: List[Dict[str, str]]) -> str:
    """
    Reason with Muse Spark for complex planning, coordination, and analysis tasks.
    Use for: planning, decision making, task decomposition, agent coordination.
    """
    client = get_meta_client()
    return await client.chat_completion(messages, model="muse-spark-1.3")


@tool
async def meta_transcribe(audio_file: str) -> str:
    """
    Transcribe audio using Muse Voice Transcribe.
    Use for: speech-to-text, voice commands, meeting transcription.
    """
    client = get_meta_client()
    return await client.transcribe(audio_file)


@tool
async def meta_generate_image(prompt: str) -> str:
    """
    Generate image using Muse Image.
    Use for: visual content creation, diagrams, illustrations, concept art.
    """
    client = get_meta_client()
    return await client.generate_image(prompt)


@tool
async def meta_segment_image(image_file: str, prompt: str = "") -> Dict[str, Any]:
    """
    Segment image using SAM 3.1.
    Use for: object detection, image segmentation, mask generation, vision analysis.
    """
    client = get_meta_client()
    return await client.segment(image_file, prompt)


@tool
async def meta_advanced_reason(messages: List[Dict[str, str]]) -> str:
    """
    Advanced reasoning with Muse Wonder.
    Use for: complex analysis, research synthesis, deep reasoning tasks.
    """
    client = get_meta_client()
    return await client.chat_completion(messages, model="muse-wonder-1.0")


@tool
async def meta_code_generate(messages: List[Dict[str, str]]) -> str:
    """
    Code generation with Muse Code.
    Use for: writing code, debugging, refactoring, code review.
    """
    client = get_meta_client()
    return await client.chat_completion(messages, model="muse-code")


# Tool list for easy registration
META_TOOLS = [
    meta_reason,
    meta_transcribe,
    meta_generate_image,
    meta_segment_image,
    meta_advanced_reason,
    meta_code_generate,
]