"""Tests for Prompt Management System"""

import pytest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.prompts import (
    PromptVersion,
    AnalysisMode,
    PromptTemplate,
    PromptManager,
    get_prompt_manager,
    render_market_analysis_prompt,
    render_stock_analysis_prompt,
    render_sentiment_analysis_prompt,
)


class TestPromptVersion:
    """Test PromptVersion enum"""
    
    def test_version_values(self):
        """Test version enum values"""
        assert PromptVersion.V1_0.value == "v1.0"
        assert PromptVersion.V1_1.value == "v1.1"
        assert PromptVersion.V2_0.value == "v2.0"
    
    def test_version_comparison(self):
        """Test version string comparison"""
        assert PromptVersion.V1_0 < PromptVersion.V1_1
        assert PromptVersion.V1_1 < PromptVersion.V2_0


class TestAnalysisMode:
    """Test AnalysisMode enum"""
    
    def test_mode_values(self):
        """Test analysis mode values"""
        assert AnalysisMode.SHORT_TERM.value == "短线T+1"
        assert AnalysisMode.MEDIUM_TERM.value == "中线"
        assert AnalysisMode.LONG_TERM.value == "长线"
        assert AnalysisMode.MARKET_OVERVIEW.value == "大盘分析"
        assert AnalysisMode.SENTIMENT.value == "情绪分析"


class TestPromptTemplate:
    """Test PromptTemplate class"""
    
    def test_template_creation(self):
        """Test creating a prompt template"""
        template = PromptTemplate(
            name="test_prompt",
            version=PromptVersion.V1_0,
            system_prompt="You are a test assistant.",
            user_template="Please answer: {question}",
            description="A test prompt",
            max_tokens=4096,
            temperature=0.7,
            output_format="text",
            tags=["test", "example"]
        )
        
        assert template.name == "test_prompt"
        assert template.version == PromptVersion.V1_0
        assert template.max_tokens == 4096
        assert template.temperature == 0.7
        assert template.output_format == "text"
        assert template.tags == ["test", "example"]
    
    def test_render_simple(self):
        """Test rendering a simple template"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="You are {role}.",
            user_template="Please answer: {question}",
            max_tokens=4096
        )
        
        system, messages = template.render(role="assistant", question="What is 2+2?")
        
        assert "You are assistant." in system
        assert "What is 2+2?" in messages[1]["content"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_render_float_formatting(self):
        """Test float value formatting"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="System",
            user_template="Price: {price}",
            max_tokens=4096
        )
        
        system, messages = template.render(price=123.456)
        
        assert "Price: 123.46" in messages[1]["content"]
    
    def test_render_list_formatting(self):
        """Test list value formatting"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="System",
            user_template="Items: {items}",
            max_tokens=4096
        )
        
        system, messages = template.render(items=["apple", "cherry", "banana"])
        
        assert "1. apple" in messages[1]["content"]
        assert "2. cherry" in messages[1]["content"]
        assert "3. banana" in messages[1]["content"]
    
    def test_render_dict_formatting(self):
        """Test dict value formatting"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="System",
            user_template="Data: {data}",
            max_tokens=4096
        )
        
        system, messages = template.render(data={"name": "test", "value": 42.5})
        
        assert "Name: test" in messages[1]["content"]
        assert "Value: 42.50" in messages[1]["content"]
    
    def test_render_empty_values(self):
        """Test handling empty values"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="System",
            user_template="List: {empty_list}, Dict: {empty_dict}",
            max_tokens=4096
        )
        
        system, messages = template.render(empty_list=[], empty_dict={})
        
        assert "无数据" in messages[1]["content"]
    
    def test_estimate_token_count(self):
        """Test token count estimation"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="System prompt " * 100,
            user_template="User prompt " * 100,
            max_tokens=4096
        )
        
        tokens = template.estimate_token_count()
        
        # Rough estimate: ~2400 chars / 4 = ~600 tokens
        assert tokens > 400
        assert tokens < 800


class TestPromptManager:
    """Test PromptManager class"""
    
    def test_manager_initialization(self):
        """Test manager initializes with default templates"""
        manager = PromptManager()
        
        templates = manager.list_templates()
        assert len(templates) == 4
        
        template_names = [t["name"] for t in templates]
        assert "market_trend_analysis" in template_names
        assert "stock_analysis_short_term" in template_names
        assert "sector_comparison" in template_names
        assert "market_sentiment_analysis" in template_names
    
    def test_get_template_latest(self):
        """Test getting latest version of a template"""
        manager = PromptManager()
        
        template = manager.get_template("market_trend_analysis")
        
        assert template is not None
        assert template.version == PromptVersion.V1_0
    
    def test_get_template_specific_version(self):
        """Test getting specific version of a template"""
        manager = PromptManager()
        
        template = manager.get_template("market_trend_analysis", PromptVersion.V1_0)
        
        assert template is not None
        assert template.version == PromptVersion.V1_0
    
    def test_get_template_not_found(self):
        """Test getting non-existent template returns None"""
        manager = PromptManager()
        
        template = manager.get_template("nonexistent")
        
        assert template is None
    
    def test_register_template(self):
        """Test registering a new template"""
        manager = PromptManager()
        
        new_template = PromptTemplate(
            name="custom_prompt",
            version=PromptVersion.V1_0,
            system_prompt="Custom system prompt",
            user_template="Custom user: {input}",
            max_tokens=4096
        )
        
        manager.register_template(new_template)
        
        retrieved = manager.get_template("custom_prompt")
        assert retrieved is not None
        assert retrieved.name == "custom_prompt"
    
    def test_list_templates_info(self):
        """Test listing all templates with info"""
        manager = PromptManager()
        
        templates = manager.list_templates()
        
        for t in templates:
            assert "name" in t
            assert "description" in t
            assert "version" in t
            assert "tags" in t
            assert "output_format" in t
    
    def test_render_prompt(self):
        """Test rendering a prompt through manager"""
        manager = PromptManager()
        
        system, messages = manager.render_prompt(
            "market_trend_analysis",
            index_code="000001",
            index_name="上证指数",
            current_price=3200.50,
            change_percent=1.25,
            kline_data="...",
            indicators_data="MACD: 金叉",
            fund_flow_data="净流入: +10亿",
            limit_up_count=50,
            limit_down_count=5,
            days=5
        )
        
        # System prompt contains analysis instructions
        assert "股票分析师" in system
        # User message contains the parameters
        assert "上证指数" in messages[1]["content"]
        assert "000001" in messages[1]["content"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_render_nonexistent_raises(self):
        """Test rendering non-existent template raises ValueError"""
        manager = PromptManager()
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            manager.render_prompt("nonexistent")
    
    def test_get_prompt_info(self):
        """Test getting prompt info"""
        manager = PromptManager()
        
        info = manager.get_prompt_info("market_trend_analysis")
        
        assert info is not None
        assert info["name"] == "market_trend_analysis"
        assert info["version"] == "v1.0"
        assert "v1.0" in info["available_versions"]


class TestConvenienceFunctions:
    """Test convenience rendering functions"""
    
    def test_render_market_analysis_prompt(self):
        """Test market analysis prompt rendering"""
        system, messages = render_market_analysis_prompt(
            index_code="000001",
            index_name="上证指数",
            current_price=3200.50,
            change_percent=1.25,
            kline_data="2026-01-29: 3200.00, 3225.60, +0.80%",
            indicators_data="MACD: 金叉, KDJ: 70",
            fund_flow_data="主力净流入: +25.6亿",
            limit_up_count=85,
            limit_down_count=5,
            days=5
        )
        
        # User message contains the parameters
        assert "上证指数" in messages[1]["content"]
        assert "000001" in messages[1]["content"]
        # System prompt contains analysis instructions
        assert "股票分析师" in system
        assert "大盘走势" in system
    
    def test_render_stock_analysis_prompt(self):
        """Test stock analysis prompt rendering"""
        system, messages = render_stock_analysis_prompt(
            stock_code="600000",
            stock_name="浦发银行",
            current_price=10.25,
            change_percent=2.15,
            change_amount=0.22,
            kline_data="2026-01-29: 10.03, 10.25, +2.28%",
            indicators_data="MACD: 底背离, KDJ: 金叉",
            fund_flow_data="主力净流入: +1.2亿",
            company_info="市盈率: 5.2, 市净率: 0.8",
            news_data="暂无重大新闻",
            sector_info="银行板块: +1.5%",
            days=5
        )
        
        # User message contains the parameters
        assert "600000" in messages[1]["content"]
        assert "浦发银行" in messages[1]["content"]
        # System prompt contains analysis instructions
        assert "短线T+1" in system
        assert "股票分析师" in system
    
    def test_render_sentiment_analysis_prompt(self):
        """Test sentiment analysis prompt rendering"""
        system, messages = render_sentiment_analysis_prompt(
            market_overview="三大指数全线上涨",
            limit_up_down_data="涨停: 85家, 跌停: 5家",
            volume_data="成交量放大20%",
            fund_flow_data="主力净流入: +50亿",
            change_distribution="涨多跌少, 上涨家数占比75%",
            sector_rotation="板块轮动较快, 热点持续1-2天"
        )
        
        assert "市场情绪" in system
        assert "涨跌停" in messages[1]["content"]


class TestPromptTokens:
    """Test token estimation and limits"""
    
    def test_token_estimate_reasonable(self):
        """Test that token estimates are reasonable"""
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            system_prompt="A" * 1000,
            user_template="B" * 1000,
            max_tokens=2000
        )
        
        tokens = template.estimate_token_count()
        
        # Should be roughly 2000/4 = 500 tokens
        assert 400 < tokens < 600


class TestPromptIntegration:
    """Integration tests for prompts module"""
    
    def test_get_prompt_manager_singleton(self):
        """Test that get_prompt_manager returns singleton"""
        manager1 = get_prompt_manager()
        manager2 = get_prompt_manager()
        
        assert manager1 is manager2
    
    def test_all_templates_renderable(self):
        """Test that all registered templates can render"""
        manager = get_prompt_manager()
        
        templates = manager.list_templates()
        
        for t in templates:
            template = manager.get_template(t["name"])
            # Should not raise exception
            system, messages = template.render(test_param="value")
            assert system is not None
            assert len(messages) == 2
    
    def test_template_versions(self):
        """Test template versioning"""
        manager = PromptManager()
        
        # All templates should be v1.0
        for name, versions in manager._templates.items():
            for version in versions.keys():
                assert version == PromptVersion.V1_0
    
    def test_template_tags(self):
        """Test that all templates have tags"""
        manager = get_prompt_manager()
        
        templates = manager.list_templates()
        
        for t in templates:
            assert len(t["tags"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
