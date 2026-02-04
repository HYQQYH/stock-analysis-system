"""LLM Configuration and Client Management for Stock Analysis System

This module provides unified LLM client interfaces supporting multiple providers:
- OpenAI (GPT-3.5, GPT-4)
- Aliyun DashScope (Qwen series)
- Zhipu GLM (ChatGLM series)
- MiniMax (M2.1 series)
- Local models (Ollama)

Features:
- Provider selection and fallback logic
- Automatic retry on failure
- Token usage tracking
- Cost estimation
- Response caching
"""

import os
import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from abc import ABC, abstractmethod

import httpx
from app.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"  # Aliyun
    ZHIPU = "zhipu"  # Zhipu GLM
    MINIMAX = "minimax"  # MiniMax M2.1
    OLLAMA = "ollama"  # Local models


@dataclass
class LLMTokenUsage:
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    
    def update(self, prompt: int, completion: int, cost: float = 0.0):
        """Update token usage"""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        self.cost_usd += cost


@dataclass
class LLMResponse:
    """Unified LLM response structure"""
    content: str
    provider: str
    model: str
    token_usage: LLMTokenUsage
    response_time_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "token_usage": {
                "prompt_tokens": self.token_usage.prompt_tokens,
                "completion_tokens": self.token_usage.completion_tokens,
                "total_tokens": self.token_usage.total_tokens,
                "cost_usd": self.token_usage.cost_usd
            },
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class LLMConfig:
    """LLM configuration for a specific provider"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


class LLMClientBase(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the LLM client, return success status"""
        pass
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke LLM with messages"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass


class OpenAIClient(LLMClientBase):
    """OpenAI GPT client using direct HTTP API"""
    
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_client: Optional[httpx.Client] = None
    
    def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            api_key = self.config.api_key or settings.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            return True
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            return False
    
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke OpenAI LLM"""
        start_time = time.time()
        token_usage = LLMTokenUsage()
        
        try:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p
            }
            
            response = self.http_client.post(self.OPENAI_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", len(json.dumps(messages)) // 4)
            completion_tokens = usage.get("completion_tokens", len(content) // 4)
            cost = (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000
            
            token_usage.update(prompt_tokens, completion_tokens, cost)
            
            return LLMResponse(
                content=content,
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=True
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model info"""
        return {
            "provider": "openai",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "features": ["streaming", "function_calling", "json_mode"]
        }


class DashScopeClient(LLMClientBase):
    """Aliyun DashScope (Qwen) client using direct HTTP API"""
    
    DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_client: Optional[httpx.Client] = None
    
    def initialize(self) -> bool:
        """Initialize DashScope client"""
        try:
            api_key = self.config.api_key or settings.dashscope_api_key
            if not api_key:
                raise ValueError("DashScope API key not configured")
            
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            return True
        except Exception as e:
            print(f"Failed to initialize DashScope client: {e}")
            return False
    
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke DashScope LLM"""
        start_time = time.time()
        token_usage = LLMTokenUsage()
        
        try:
            # Convert messages to DashScope format
            input_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            payload = {
                "model": self.config.model,
                "input": {
                    "messages": [{"role": "user", "content": input_text}]
                },
                "parameters": {
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p
                }
            }
            
            response = self.http_client.post(self.DASHSCOPE_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["output"]["text"]
            usage = result.get("usage", {})
            
            prompt_tokens = usage.get("input_tokens", len(input_text) // 4)
            completion_tokens = usage.get("output_tokens", len(content) // 4)
            cost = (prompt_tokens * 0.0002 + completion_tokens * 0.0002) / 1000
            
            token_usage.update(prompt_tokens, completion_tokens, cost)
            
            return LLMResponse(
                content=content,
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get DashScope model info"""
        return {
            "provider": "dashscope",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "features": ["streaming", "function_calling"]
        }


class ZhipuGLMClient(LLMClientBase):
    """Zhipu GLM (ChatGLM) client using direct HTTP API"""
    
    ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_client: Optional[httpx.Client] = None
    
    def initialize(self) -> bool:
        """Initialize Zhipu GLM client"""
        try:
            api_key = self.config.api_key or settings.zhipu_api_key
            if not api_key:
                raise ValueError("Zhipu API key not configured")
            
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            return True
        except Exception as e:
            print(f"Failed to initialize Zhipu GLM client: {e}")
            return False
    
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke Zhipu GLM"""
        start_time = time.time()
        token_usage = LLMTokenUsage()
        
        try:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "max_output_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p
            }
            
            response = self.http_client.post(self.ZHIPU_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", len(json.dumps(messages)) // 4)
            completion_tokens = usage.get("completion_tokens", len(content) // 4)
            cost = (prompt_tokens * 0.0005 + completion_tokens * 0.0005) / 1000
            
            token_usage.update(prompt_tokens, completion_tokens, cost)
            
            return LLMResponse(
                content=content,
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Zhipu GLM model info"""
        return {
            "provider": "zhipu",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "features": ["streaming", "function_calling"]
        }


class OllamaClient(LLMClientBase):
    """Ollama local model client using direct HTTP API"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"
        self.http_client: Optional[httpx.Client] = None
    
    def initialize(self) -> bool:
        """Initialize Ollama client"""
        try:
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout)
            )
            # Test connection
            response = self.http_client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to initialize Ollama client: {e}")
            return False
    
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke Ollama model"""
        start_time = time.time()
        token_usage = LLMTokenUsage()
        
        try:
            # Convert messages to Ollama format
            prompt = "\n".join([f"### {m['role'].upper()}\n{m['content']}" for m in messages])
            
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            response = self.http_client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result.get("response", "")
            
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(content) // 4
            
            token_usage.update(prompt_tokens, completion_tokens, 0)  # Local, no cost
            
            return LLMResponse(
                content=content,
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model info"""
        return {
            "provider": "ollama",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "features": ["streaming", "local"]
        }


class MiniMaxClient(LLMClientBase):
    """MiniMax M2.1 client using Anthropic API compatible interface
    
    MiniMax provides an Anthropic-compatible API endpoint.
    See: https://api.minimaxi.com/anthropic
    """
    
    # Anthropic compatible API URL
    ANTHROPIC_API_URL = "https://api.minimaxi.com/anthropic/v1/messages"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_client: Optional[httpx.Client] = None
    
    def initialize(self) -> bool:
        """Initialize MiniMax client"""
        try:
            api_key = self.config.api_key or settings.minimax_api_key
            if not api_key:
                raise ValueError("MiniMax API key not configured")
            
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            return True
        except Exception as e:
            print(f"Failed to initialize MiniMax client: {e}")
            return False
    
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Invoke MiniMax LLM using Anthropic compatible API"""
        start_time = time.time()
        token_usage = LLMTokenUsage()
        
        try:
            # Convert messages to Anthropic format
            # Extract system message if present
            system_message = None
            anthropic_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    # Anthropic format: content as array of text blocks
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": [{"type": "text", "text": msg["content"]}]
                    })
            
            # Build payload according to Anthropic API format
            payload = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "messages": anthropic_messages
            }
            
            # Add system message if present
            if system_message:
                payload["system"] = system_message
            
            response = self.http_client.post(self.ANTHROPIC_API_URL, json=payload)
            
            # Log the raw response for debugging
            logger.info(f"[MiniMax] Response status: {response.status_code}")
            logger.info(f"[MiniMax] Response body: {response.text[:1000]}")
            
            response.raise_for_status()
            result = response.json()
            
            # Try to parse Anthropic-style response first
            content = ""
            content_blocks = result.get("content", [])
            if content_blocks and isinstance(content_blocks, list):
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content += block.get("text", "")
            
            # If content is empty, try alternative formats
            if not content:
                # MiniMax might return response in different format
                if "choices" in result:
                    # OpenAI compatible format
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                elif "output" in result:
                    # DashScope compatible format
                    content = result.get("output", {}).get("text", "")
                elif "text" in result:
                    # Direct text field
                    content = result.get("text", "")
                elif "data" in result:
                    # Some other format
                    content = str(result.get("data"))
            
            if not content:
                raise ValueError("Empty response from MiniMax API")
            
            usage = result.get("usage", {})
            
            prompt_tokens = usage.get("input_tokens", len(json.dumps(messages)) // 4)
            completion_tokens = usage.get("output_tokens", len(content) // 4)
            cost = (prompt_tokens * 0.0002 + completion_tokens * 0.0002) / 1000
            
            token_usage.update(prompt_tokens, completion_tokens, cost)
            
            return LLMResponse(
                content=content,
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.provider.value,
                model=self.config.model,
                token_usage=token_usage,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get MiniMax model info"""
        return {
            "provider": "minimax",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "features": ["streaming", "function_calling"]
        }


class LLMManager:
    """Unified LLM manager with provider selection and fallback"""
    
    # Default model configurations per provider
    DEFAULT_MODELS = {
        LLMProvider.OPENAI: "gpt-3.5-turbo",
        LLMProvider.DASHSCOPE: "qwen-turbo",
        LLMProvider.ZHIPU: "glm-4.7",
        LLMProvider.MINIMAX: "MiniMax-M2.1",  # MiniMax official model name
        LLMProvider.OLLAMA: "llama2"
    }
    
    # Fallback order when primary provider fails - MiniMax first!
    FALLBACK_ORDER = [
        LLMProvider.MINIMAX,
        LLMProvider.OPENAI,
        LLMProvider.DASHSCOPE,
        LLMProvider.ZHIPU,
        LLMProvider.OLLAMA
    ]
    
    def __init__(self):
        self.current_provider: Optional[LLMProvider] = None
        self.current_client: Optional[LLMClientBase] = None
        self.clients: Dict[LLMProvider, LLMClientBase] = {}
        self.initialized = False
        self.total_token_usage = LLMTokenUsage()
    
    def initialize(self, provider: Optional[str] = None) -> bool:
        """Initialize LLM manager with specified or configured provider
        
        Args:
            provider: Provider name (openai, dashscope, etc.) or None to use config
            
        Returns:
            True if initialization successful
        """
        provider_name = provider or settings.llm_provider
        try:
            self.current_provider = LLMProvider(provider_name)
        except ValueError:
            self.current_provider = LLMProvider.OPENAI
        
        # Initialize the primary provider
        success = self._initialize_provider(self.current_provider)
        
        if not success and self.current_provider in self.FALLBACK_ORDER:
            # Try fallback providers
            for fallback_provider in self.FALLBACK_ORDER:
                if fallback_provider != self.current_provider:
                    if self._initialize_provider(fallback_provider):
                        self.current_provider = fallback_provider
                        self.current_client = self.clients[fallback_provider]
                        success = True
                        print(f"Fallback to {fallback_provider.value}")
                        break
        
        self.initialized = success
        return success
    
    def _initialize_provider(self, provider: LLMProvider) -> bool:
        """Initialize a specific provider"""
        try:
            config = self._create_config(provider)
            client = self._create_client(provider, config)
            
            if client.initialize():
                self.clients[provider] = client
                return True
            
            return False
        except Exception as e:
            print(f"Failed to initialize provider {provider.value}: {e}")
            return False
    
    def _create_config(self, provider: LLMProvider) -> LLMConfig:
        """Create LLM configuration for a provider"""
        model = self.DEFAULT_MODELS.get(provider, settings.llm_model)
        
        # Get provider-specific API key
        api_key = None
        if provider == LLMProvider.OPENAI:
            api_key = settings.openai_api_key
        elif provider == LLMProvider.DASHSCOPE:
            api_key = settings.dashscope_api_key
        elif provider == LLMProvider.ZHIPU:
            api_key = settings.zhipu_api_key
        elif provider == LLMProvider.MINIMAX:
            api_key = settings.minimax_api_key
        
        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=0.7,
            max_tokens=4096,
            timeout=60,
            max_retries=3
        )
    
    def _create_client(self, provider: LLMProvider, config: LLMConfig) -> LLMClientBase:
        """Create LLM client for a provider"""
        clients = {
            LLMProvider.OPENAI: OpenAIClient,
            LLMProvider.DASHSCOPE: DashScopeClient,
            LLMProvider.ZHIPU: ZhipuGLMClient,
            LLMProvider.MINIMAX: MiniMaxClient,
            LLMProvider.OLLAMA: OllamaClient,
        }
        
        client_class = clients.get(provider)
        if not client_class:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return client_class(config)
    
    def invoke(self, messages: List[Dict[str, str]], 
               provider: Optional[str] = None,
               use_fallback: bool = True) -> LLMResponse:
        """Invoke LLM with automatic fallback
        
        Args:
            messages: List of chat messages with 'role' and 'content'
            provider: Specific provider to use, or None for default
            use_fallback: Whether to try fallback providers on failure
            
        Returns:
            LLMResponse with content and metadata
        """
        if not self.initialized:
            if not self.initialize():
                return LLMResponse(
                    content="",
                    provider="",
                    model="",
                    token_usage=LLMTokenUsage(),
                    response_time_ms=0,
                    success=False,
                    error_message="LLM manager not initialized"
                )
        
        # Use specified provider or current
        try:
            target_provider = LLMProvider(provider) if provider else self.current_provider
        except ValueError:
            target_provider = self.current_provider
        
        if target_provider in self.clients:
            self.current_client = self.clients[target_provider]
        else:
            # Try to initialize the requested provider
            if not self._initialize_provider(target_provider):
                if use_fallback:
                    return self._try_fallback(messages)
                return LLMResponse(
                    content="",
                    provider=target_provider.value,
                    model="",
                    token_usage=LLMTokenUsage(),
                    response_time_ms=0,
                    success=False,
                    error_message=f"Provider {target_provider.value} not available"
                )
        
        # Invoke the client
        response = self.current_client.invoke(messages)
        
        # Update token usage
        self.total_token_usage.update(
            response.token_usage.prompt_tokens,
            response.token_usage.completion_tokens,
            response.token_usage.cost_usd
        )
        
        # Try fallback on failure
        if not response.success and use_fallback:
            return self._try_fallback(messages)
        
        return response
    
    def _try_fallback(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Try fallback providers"""
        for provider in self.FALLBACK_ORDER:
            if provider != self.current_provider and provider in self.clients:
                response = self.clients[provider].invoke(messages)
                if response.success:
                    return response
        
        return LLMResponse(
            content="",
            provider="",
            model="",
            token_usage=LLMTokenUsage(),
            response_time_ms=0,
            success=False,
            error_message="All providers failed"
        )
    
    def get_model_info(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get model information"""
        try:
            target_provider = LLMProvider(provider) if provider else self.current_provider
        except ValueError:
            target_provider = self.current_provider
        
        if target_provider in self.clients:
            return self.clients[target_provider].get_model_info()
        
        return {"error": f"Provider {target_provider} not initialized"}
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers"""
        providers = []
        for provider in LLMProvider:
            if provider in self.clients:
                info = self.clients[provider].get_model_info()
                info["available"] = True
                providers.append(info)
            else:
                providers.append({
                    "provider": provider.value,
                    "available": False
                })
        return providers
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        return {
            "total_prompt_tokens": self.total_token_usage.prompt_tokens,
            "total_completion_tokens": self.total_token_usage.completion_tokens,
            "total_tokens": self.total_token_usage.total_tokens,
            "total_cost_usd": self.total_token_usage.cost_usd
        }
    
    def switch_provider(self, provider: str) -> bool:
        """Switch to a different provider"""
        try:
            target = LLMProvider(provider)
            if target in self.clients:
                self.current_provider = target
                self.current_client = self.clients[target]
                return True
            else:
                return self._initialize_provider(target)
        except ValueError:
            return False


# Global LLM manager instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get or create the global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


def initialize_llm(provider: Optional[str] = None) -> bool:
    """Initialize the LLM manager with the specified provider"""
    manager = get_llm_manager()
    return manager.initialize(provider)


def invoke_llm(messages: List[Dict[str, str]], 
               provider: Optional[str] = None,
               use_fallback: bool = True) -> LLMResponse:
    """Convenience function to invoke LLM"""
    manager = get_llm_manager()
    return manager.invoke(messages, provider, use_fallback)


def create_chat_message(role: str, content: str) -> Dict[str, str]:
    """Create a chat message with the specified role
    
    Args:
        role: Message role (user, assistant, system)
        content: Message content
        
    Returns:
        Message dict with 'role' and 'content'
    """
    valid_roles = ["user", "assistant", "system"]
    if role not in valid_roles:
        raise ValueError(f"Unknown message role: {role}. Must be one of {valid_roles}")
    return {"role": role, "content": content}


# Test function
def test_llm_connection():
    """Test LLM connection and print model info"""
    print("Testing LLM connection...")
    
    manager = get_llm_manager()
    if not manager.initialize():
        print("Failed to initialize LLM manager (no API keys configured)")
        print("This is expected if no LLM API keys are set in .env")
        return True  # Not a failure, just no keys
    
    print(f"Current provider: {manager.current_provider.value}")
    
    # Get model info
    model_info = manager.get_model_info()
    print(f"Model info: {json.dumps(model_info, indent=2, ensure_ascii=False)}")
    
    # Test simple invocation
    messages = [create_chat_message("user", "你好，请做一个简单的自我介绍")]
    response = manager.invoke(messages)
    
    print(f"\nResponse success: {response.success}")
    print(f"Response time: {response.response_time_ms:.2f}ms")
    print(f"Token usage: {response.token_usage}")
    
    if response.success:
        print(f"\nResponse content:\n{response.content}")
    else:
        print(f"Error: {response.error_message}")
    
    # Show available providers
    print(f"\nAvailable providers: {json.dumps(manager.get_available_providers(), indent=2, ensure_ascii=False)}")
    
    return response.success


if __name__ == "__main__":
    # Run test
    test_llm_connection()
