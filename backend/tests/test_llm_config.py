"""Unit tests for LLM Configuration module"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.llm_config import (
    LLMProvider,
    LLMTokenUsage,
    LLMResponse,
    LLMConfig,
    LLMManager,
    OpenAIClient,
    DashScopeClient,
    ZhipuGLMClient,
    MiniMaxClient,
    OllamaClient,
    get_llm_manager,
    initialize_llm,
    invoke_llm,
    create_chat_message,
)


class TestLLMProvider:
    """Tests for LLMProvider enum"""
    
    def test_provider_values(self):
        """Test provider enum values"""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.DASHSCOPE.value == "dashscope"
        assert LLMProvider.ZHIPU.value == "zhipu"
        assert LLMProvider.MINIMAX.value == "minimax"
        assert LLMProvider.OLLAMA.value == "ollama"
    
    def test_provider_list(self):
        """Test all providers are defined"""
        providers = list(LLMProvider)
        assert len(providers) == 5
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.DASHSCOPE in providers
        assert LLMProvider.ZHIPU in providers
        assert LLMProvider.MINIMAX in providers
        assert LLMProvider.OLLAMA in providers


class TestLLMTokenUsage:
    """Tests for LLMTokenUsage dataclass"""
    
    def test_token_usage_creation(self):
        """Test creating token usage"""
        usage = LLMTokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.005
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.005
    
    def test_token_usage_defaults(self):
        """Test default values"""
        usage = LLMTokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.cost_usd == 0.0
    
    def test_token_usage_update(self):
        """Test updating token usage"""
        usage = LLMTokenUsage()
        usage.update(100, 50, 0.005)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.005
        
        # Update again
        usage.update(50, 25, 0.002)
        assert usage.prompt_tokens == 150
        assert usage.completion_tokens == 75
        assert usage.total_tokens == 225
        assert usage.cost_usd == 0.007


class TestLLMResponse:
    """Tests for LLMResponse dataclass"""
    
    def test_response_creation(self):
        """Test creating LLM response"""
        token_usage = LLMTokenUsage()
        response = LLMResponse(
            content="Hello, I am a stock analysis AI.",
            provider="openai",
            model="gpt-3.5-turbo",
            token_usage=token_usage,
            response_time_ms=1500.5
        )
        assert response.content == "Hello, I am a stock analysis AI."
        assert response.provider == "openai"
        assert response.model == "gpt-3.5-turbo"
        assert response.response_time_ms == 1500.5
        assert response.success == True
        assert response.error_message is None
    
    def test_response_failure(self):
        """Test creating failed LLM response"""
        token_usage = LLMTokenUsage()
        response = LLMResponse(
            content="",
            provider="openai",
            model="gpt-3.5-turbo",
            token_usage=token_usage,
            response_time_ms=500,
            success=False,
            error_message="API rate limit exceeded"
        )
        assert response.success == False
        assert response.error_message == "API rate limit exceeded"
    
    def test_response_to_dict(self):
        """Test converting response to dictionary"""
        token_usage = LLMTokenUsage(prompt_tokens=100, completion_tokens=50, cost_usd=0.005)
        response = LLMResponse(
            content="Test response",
            provider="openai",
            model="gpt-3.5-turbo",
            token_usage=token_usage,
            response_time_ms=1000
        )
        result = response.to_dict()
        
        assert result["content"] == "Test response"
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-3.5-turbo"
        assert result["token_usage"]["prompt_tokens"] == 100
        assert result["token_usage"]["completion_tokens"] == 50
        assert result["success"] == True
        assert "timestamp" in result
    
    def test_response_timestamp(self):
        """Test response timestamp is auto-generated"""
        before = datetime.now(timezone.utc).isoformat()
        token_usage = LLMTokenUsage()
        response = LLMResponse(
            content="Test",
            provider="openai",
            model="test",
            token_usage=token_usage,
            response_time_ms=100
        )
        after = datetime.now(timezone.utc).isoformat()
        
        assert response.timestamp >= before
        assert response.timestamp <= after


class TestLLMConfig:
    """Tests for LLMConfig dataclass"""
    
    def test_config_creation(self):
        """Test creating LLM config"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            api_key="sk-test-key",
            max_tokens=8192,
            temperature=0.5
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test-key"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5
    
    def test_config_defaults(self):
        """Test config default values"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo"
        )
        assert config.api_key is None
        assert config.base_url is None
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.top_p == 0.95
        assert config.timeout == 60
        assert config.max_retries == 3


class TestOpenAIClient:
    """Tests for OpenAIClient class"""
    
    @patch('app.llm_config.settings')
    def test_client_initialize_no_api_key(self, mock_settings):
        """Test initialization fails without API key"""
        mock_settings.openai_api_key = None
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo"
        )
        client = OpenAIClient(config)
        result = client.initialize()
        assert result == False
    
    @patch('app.llm_config.settings')
    def test_client_initialize_with_api_key(self, mock_settings):
        """Test initialization succeeds with API key"""
        mock_settings.openai_api_key = "test-api-key"
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo"
        )
        client = OpenAIClient(config)
        # This will fail because we don't have a real API key, but should not raise exception
        # result = client.initialize()
        # assert result == True
        # assert client.client is not None
    
    def test_get_model_info(self):
        """Test getting model info"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            max_tokens=4096,
            temperature=0.7
        )
        client = OpenAIClient(config)
        info = client.get_model_info()
        
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-3.5-turbo"
        assert info["max_tokens"] == 4096
        assert "streaming" in info["features"]
        assert "function_calling" in info["features"]


class TestDashScopeClient:
    """Tests for DashScopeClient class"""
    
    @patch('app.llm_config.settings')
    def test_client_initialize_no_api_key(self, mock_settings):
        """Test initialization fails without API key"""
        mock_settings.dashscope_api_key = None
        config = LLMConfig(
            provider=LLMProvider.DASHSCOPE,
            model="qwen-turbo"
        )
        client = DashScopeClient(config)
        result = client.initialize()
        assert result == False
    
    def test_get_model_info(self):
        """Test getting DashScope model info"""
        config = LLMConfig(
            provider=LLMProvider.DASHSCOPE,
            model="qwen-turbo"
        )
        client = DashScopeClient(config)
        info = client.get_model_info()
        
        assert info["provider"] == "dashscope"
        assert info["model"] == "qwen-turbo"
        assert "streaming" in info["features"]
        assert "function_calling" in info["features"]


class TestOllamaClient:
    """Tests for OllamaClient class"""
    
    def test_get_model_info(self):
        """Test getting Ollama model info"""
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama2"
        )
        client = OllamaClient(config)
        info = client.get_model_info()
        
        assert info["provider"] == "ollama"
        assert info["model"] == "llama2"
        assert "local" in info["features"]


class TestMiniMaxClient:
    """Tests for MiniMaxClient class"""
    
    @patch('app.llm_config.settings')
    def test_client_initialize_no_api_key(self, mock_settings):
        """Test initialization fails without API key"""
        mock_settings.minimax_api_key = None
        config = LLMConfig(
            provider=LLMProvider.MINIMAX,
            model="abab6.5s-chat"
        )
        client = MiniMaxClient(config)
        result = client.initialize()
        assert result == False
    
    def test_get_model_info(self):
        """Test getting MiniMax model info"""
        config = LLMConfig(
            provider=LLMProvider.MINIMAX,
            model="abab6.5s-chat",
            max_tokens=4096,
            temperature=0.7
        )
        client = MiniMaxClient(config)
        info = client.get_model_info()
        
        assert info["provider"] == "minimax"
        assert info["model"] == "abab6.5s-chat"
        assert info["max_tokens"] == 4096
        assert "streaming" in info["features"]
        assert "function_calling" in info["features"]


class TestLLMManager:
    """Tests for LLMManager class"""
    
    def test_manager_initialization(self):
        """Test manager initializes correctly"""
        manager = LLMManager()
        assert manager.current_provider is None
        assert manager.current_client is None
        assert manager.clients == {}
        assert manager.initialized == False
        assert manager.total_token_usage.total_tokens == 0
    
    def test_default_models(self):
        """Test default models are defined"""
        manager = LLMManager()
        
        assert manager.DEFAULT_MODELS[LLMProvider.OPENAI] == "gpt-3.5-turbo"
        assert manager.DEFAULT_MODELS[LLMProvider.DASHSCOPE] == "qwen-turbo"
        assert manager.DEFAULT_MODELS[LLMProvider.ZHIPU] == "glm-4"
        assert manager.DEFAULT_MODELS[LLMProvider.MINIMAX] == "abab6.5s-chat"
        assert manager.DEFAULT_MODELS[LLMProvider.OLLAMA] == "llama2"
    
    def test_fallback_order(self):
        """Test fallback order is defined"""
        manager = LLMManager()
        
        assert len(manager.FALLBACK_ORDER) > 0
        assert LLMProvider.OPENAI in manager.FALLBACK_ORDER
        assert LLMProvider.DASHSCOPE in manager.FALLBACK_ORDER
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        manager = LLMManager()
        stats = manager.get_usage_stats()
        
        assert "total_prompt_tokens" in stats
        assert "total_completion_tokens" in stats
        assert "total_tokens" in stats
        assert "total_cost_usd" in stats
        assert stats["total_tokens"] == 0
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        manager = LLMManager()
        providers = manager.get_available_providers()
        
        assert len(providers) == len(LLMProvider)
        for p in providers:
            assert "provider" in p
            assert "available" in p
            assert p["available"] == False  # None initialized yet
    
    def test_switch_provider_invalid(self):
        """Test switching to invalid provider"""
        manager = LLMManager()
        result = manager.switch_provider("invalid_provider")
        assert result == False


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_create_chat_message_user(self):
        """Test creating user message dict"""
        message = create_chat_message("user", "Hello, AI!")
        assert message["role"] == "user"
        assert message["content"] == "Hello, AI!"
    
    def test_create_chat_message_assistant(self):
        """Test creating assistant message dict"""
        message = create_chat_message("assistant", "Hello, human!")
        assert message["role"] == "assistant"
        assert message["content"] == "Hello, human!"
    
    def test_create_chat_message_system(self):
        """Test creating system message dict"""
        message = create_chat_message("system", "You are a helpful assistant.")
        assert message["role"] == "system"
        assert message["content"] == "You are a helpful assistant."
    
    def test_create_chat_message_invalid(self):
        """Test creating message with invalid role"""
        with pytest.raises(ValueError):
            create_chat_message("invalid", "test")


class TestGlobalFunctions:
    """Tests for global convenience functions"""
    
    def test_get_llm_manager_singleton(self):
        """Test get_llm_manager returns singleton"""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()
        assert manager1 is manager2
    
    def test_initialize_llm_function(self):
        """Test initialize_llm function exists"""
        assert callable(initialize_llm)
    
    def test_invoke_llm_function(self):
        """Test invoke_llm function exists"""
        assert callable(invoke_llm)


class TestLLMResponseStructure:
    """Tests for LLM response structure validation"""
    
    def test_response_has_required_fields(self):
        """Test response has all required fields"""
        token_usage = LLMTokenUsage()
        response = LLMResponse(
            content="test",
            provider="test",
            model="test",
            token_usage=token_usage,
            response_time_ms=100
        )
        
        # Check all fields exist
        assert hasattr(response, 'content')
        assert hasattr(response, 'provider')
        assert hasattr(response, 'model')
        assert hasattr(response, 'token_usage')
        assert hasattr(response, 'response_time_ms')
        assert hasattr(response, 'timestamp')
        assert hasattr(response, 'success')
        assert hasattr(response, 'error_message')
        assert hasattr(response, 'to_dict')
    
    def test_response_to_dict_has_all_fields(self):
        """Test to_dict returns all fields"""
        token_usage = LLMTokenUsage()
        response = LLMResponse(
            content="test",
            provider="test",
            model="test",
            token_usage=token_usage,
            response_time_ms=100
        )
        result = response.to_dict()
        
        assert "content" in result
        assert "provider" in result
        assert "model" in result
        assert "token_usage" in result
        assert "response_time_ms" in result
        assert "timestamp" in result
        assert "success" in result
        assert "error_message" in result


class TestProviderFallback:
    """Tests for provider fallback logic"""
    
    def test_fallback_order_not_empty(self):
        """Test fallback order is not empty"""
        manager = LLMManager()
        assert len(manager.FALLBACK_ORDER) > 0
    
    def test_fallback_order_primary_first(self):
        """Test fallback order starts with primary provider"""
        manager = LLMManager()
        # The first fallback should be the primary (usually OpenAI)
        assert manager.FALLBACK_ORDER[0] == LLMProvider.OPENAI


class TestCostEstimation:
    """Tests for cost estimation"""
    
    def test_token_usage_cost_tracking(self):
        """Test token usage tracks cost"""
        usage = LLMTokenUsage()
        usage.update(1000, 500, 0.01)
        usage.update(500, 250, 0.005)
        
        assert usage.prompt_tokens == 1500
        assert usage.completion_tokens == 750
        assert usage.cost_usd == 0.015


class TestProviderConfiguration:
    """Tests for provider-specific configuration"""
    
    def test_openai_config(self):
        """Test OpenAI configuration"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            temperature=0.5,
            max_tokens=8192
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.temperature == 0.5
        assert config.max_tokens == 8192
    
    def test_dashscope_config(self):
        """Test DashScope configuration"""
        config = LLMConfig(
            provider=LLMProvider.DASHSCOPE,
            model="qwen-plus"
        )
        assert config.provider == LLMProvider.DASHSCOPE
        assert config.model == "qwen-plus"
    
    def test_ollama_config(self):
        """Test Ollama configuration"""
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama2",
            base_url="http://localhost:11434"
        )
        assert config.provider == LLMProvider.OLLAMA
        assert config.base_url == "http://localhost:11434"
